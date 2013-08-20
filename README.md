timeline_ift
=============

This script takes input data from a coded spreadsheet with
foraging information in it and a processed Fluorite log with
Eclipse commands in it and then creates a visual timeline
of the participant's actions.

This script is pretty quick-and-dirty, so it's not using a lot
of best practices. For example it doesn't use CSS (which would
help the visual presentation a lot) and it doesn't really lay
out items in most user-friendly way (ex: text always on top).

Inputs
---

Place in the data directory:

- A codes file in tab-separated format, usually
copy-pastable from Excel, ex: p03-coded.txt

- A commands file in tab-separated format, usually
copy-pastable from Excel, ex: p03-commands.txt

Output
---

- An SVG file of the timeline, ex: p03.svg

Copyright
===

Copyright (c) 2013, Iriwn Kwan All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer. Redistributions in binary
form must reproduce the above copyright notice, this list of conditions and
the following disclaimer in the documentation and/or other materials provided
with the distribution. Neither the name of the <ORGANIZATION> nor the names of
its contributors may be used to endorse or promote products derived from this
software without specific prior written permission. THIS SOFTWARE IS PROVIDED
BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

