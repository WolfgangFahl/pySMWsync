"""
Regression test for the scholarsync "destroys existing values" bug
(2026-07-04, see Tool/scholarsync).

When Wikidata has no value for a property, sync() must NOT overwrite the
existing page value with an empty string - it must skip the edit entirely.

This test is network-free: SyncCmd.__init__ (which needs a live wiki) is
bypassed and the collaborators are mocked, so it also runs in public CI.
"""
import unittest
from unittest.mock import MagicMock, patch

from smwsync.synccmd import SyncCmd


class TestSyncNoOverwrite(unittest.TestCase):
    """
    sync() must never blank an existing page value
    """

    def _make_synccmd(self, wd_value):
        cmd = SyncCmd.__new__(SyncCmd)
        cmd.debug = False
        cmd.verbose = False
        cmd.progress = False
        cmd.dry = False
        cmd.wikiId = "test"
        cmd.color_msg = lambda *a, **k: None
        cmd.getValue = MagicMock(return_value=wd_value)
        cmd.readItemsFromCache = MagicMock(
            return_value={"row": {"orcid": "Q1", "Scholar": "Some Scholar"}}
        )
        pk_map = MagicMock(smw_prop="orcid")
        pm = MagicMock(pid="P6178", smw_prop="researchGate")
        tm = MagicMock(topic_name="Scholar")
        tm.getPkSMWPropMap.return_value = pk_map
        tm.getPmForArg.return_value = pm
        cmd.mapping = MagicMock()
        cmd.mapping.map_by_topic = {"Scholar": tm}
        return cmd

    def _run(self, wd_value):
        cmd = self._make_synccmd(wd_value)
        topic = MagicMock()
        topic.name = "Scholar"
        with patch("smwsync.synccmd.WikiPush") as WikiPushMock:
            wikipush = WikiPushMock.return_value
            cmd.sync(topic, pk="qid", pk_values=None, prop_arglist=["research"])
            return wikipush.edit_wikison

    def test_none_value_does_not_overwrite(self):
        """a missing Wikidata value must not trigger an edit"""
        edit = self._run(None)
        edit.assert_not_called()

    def test_present_value_is_written(self):
        """a present Wikidata value is written through unchanged"""
        edit = self._run("Robert-David-13")
        edit.assert_called_once()
        _, kwargs = edit.call_args
        self.assertEqual("Robert-David-13", kwargs["value"])
        self.assertEqual("researchGate", kwargs["property_name"])


if __name__ == "__main__":
    unittest.main()
