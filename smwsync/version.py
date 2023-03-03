'''
Created on 2022-09-11

@author: wf
'''
import smwsync
class Version(object):
    """
    Version handling for pySMWSync
    """
    name = "pySMWSync"
    version = smwsync.__version__
    date = '2023-03-03'
    updated = '2023-03-03'
    description = 'synchronize Semantic MediaWiki content e.g. with wikidata',
    
    authors = 'Wolfgang Fahl'
    
    doc_url="https://wiki.bitplan.com/index.php/pySMWSync"
    chat_url="https://github.com/WolfgangFahl/pySMWSync/discussions"
    cm_url="https://github.com/WolfgangFahl/pySMWSync"

    license = f'''Copyright 2023 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.'''
    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""