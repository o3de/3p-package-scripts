#
# All or portions of this file Copyright (c) Amazon.com, Inc. or its affiliates or
# its licensors.
#
# For complete copyright and license terms please see the LICENSE at the root of this
# distribution (the "License"). All use of this software is governed by the License,
# or, if provided, by the license below or the license accompanying this file. Do not
# remove or modify any license notices. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import argparse

from common import CommonUtils

"""A CLI utility to print the list of packages in the config files."""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lists all packages in the package manifest files')
    CommonUtils.AddCommonArgs(parser)
    args = parser.parse_args()
    CommonUtils.PostArgParse(args)

    data = CommonUtils.LoadPackageLists(args.search_path)

    CommonUtils.PrintPackageList(data)
    
