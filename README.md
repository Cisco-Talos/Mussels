# Mussels

```
  __    __     __  __     ______     ______     ______     __         ______    
 /\ "-./  \   /\ \/\ \   /\  ___\   /\  ___\   /\  ___\   /\ \       /\  ___\   
 \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \___  \  \ \  __\   \ \ \____  \ \___  \  
  \ \_\ \ \_\  \ \_____\  \/\_____\  \/\_____\  \ \_____\  \ \_____\  \/\_____\ 
   \/_/  \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/ 
```

A tool to download, build, and assemble application dependencies.
                                    Brought to you by the Clam AntiVirus Team.

Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Usage

usage: mussels.py [-h] [--build {all,curl,nghttp2,openssl,pthreads,zlib}]
                  [--notemp]

optional arguments:
  -h, --help            show this help message and exit
  --build {all,curl,nghttp2,openssl,pthreads,zlib}
                        Choose a specific target you wish to build.
  --notemp              Uses the current working directory instead of a temp
                        directory.
