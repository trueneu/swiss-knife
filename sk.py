#!/usr/bin/env python
"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

mailto: true.neu@gmail.com
"""

import os
from sk import swiss_knife


def main():
    cwd = os.getcwd()
    sk_dir = os.path.dirname(os.path.abspath(__file__))
    sk_path = __file__
    sk = swiss_knife.SwissKnife(cwd=cwd, sk_dir=sk_dir, sk_path=sk_path)
    sk.run()

if __name__ == "__main__":
    main()
