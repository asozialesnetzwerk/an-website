# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# pylint: disable=wrong-import-position

"""Nobody inspects the spammish repetition."""

from __future__ import annotations

import contextlib
import os
import sys
import tracemalloc
import warnings

from setproctitle import getproctitle

getproctitle()  # 42

if sys.flags.dev_mode and not (
    "PYTHONWARNINGS" in os.environ or " -W" in " ".join(sys.orig_argv)
):
    warnings.simplefilter("error", SyntaxWarning)
    warnings.simplefilter("error", RuntimeWarning)
    warnings.simplefilter("error", EncodingWarning)
    warnings.simplefilter("error", DeprecationWarning)
warnings.filterwarnings("ignore", module="defusedxml")
warnings.filterwarnings("ignore", module="dill._dill", category=EncodingWarning)


from . import patches

patches.apply()


from .main import main

if __name__ == "__main__":
    if sys.flags.dev_mode:
        tracemalloc.start()
        if sys.version_info >= (3, 12):
            with contextlib.suppress(ValueError):
                sys.activate_stack_trampoline("perf")

    sys.exit(main())
