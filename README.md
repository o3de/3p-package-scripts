# Simple Package System

This document is an introduction to the simple package system used here.  It covers package authoring and lightly touches on package usage on the other side (i.e. in code bases that need the packages).  For more details on the package-consumer side, see documentation on the consumer side repository regarding using the package system.

This directory contains scripts used for the *authoring* of simple packages containing pre-built binaries (as opposed to source packages).

Everything required to unpack and use a package created with this system is already present in CMake, and thus *using* one of these packages adds no additional 3rd Party requirements such as a python installation.

*Authoring* the packages is done via python scripts, and thus a Python 3 interpreter must be installed in order to author packages.  In addition, specific packages that build from source code may have additional build requirements.  The build scripts or documentation for those packages will note the requirements.

### Requirements
If you intend to upload packages to S3, the upload scripts also require the boto3 pip package installed as well as certifi certificate packages. ('pip install boto3 certifi').

## Structure of a Package - Authoring Side

The workflow for authoring a package involves creating a folder containing the "Image" of the package to be packed up, then running scripts on that folder to pack it up and generate hashes for the files present.

The package system scripts here are NOT intended to be a fully functional package repository and building script system - instead, it focuses on just packing up prepared folder structures into zip files and verifying their hashes.  Instead of trying to create yet another build system, it leans on existing package build systems like 'vcpkg' to build package folder images.

On the **authoring** side, a package image (ready to pack) is valid as long as there are at least two files present:
 - PackageInfo.json, which describes the package (and must be at the root folder of the package)
 - A license file (such as LICENSE.TXT) that contains the license information.  This file can be anywhere in the package.

The PackageInfo "LicenseFile" field must point at the license file, relative to where the PackageInfo.json file is.  The PackageInfo 'PackageName' field uniquely identifies a package and is also a unique key for it in terms of uploading / downloading.  The "License field must be a SPDX license identifier or the word "Custom".

```json
{
    "PackageName" : "zlib-1.2.8-multiplatform",
    "URL"         : "https://zlib.net",
    "License"     : "zlib",
    "LicenseFile" : "zlib/LICENSE"
}
```
Note that 'PackageName' is a full identifier of the package and must be unique across all packages used.   This is why it includes its name, version, and platform(s) its meant for.

If the PackageInfo.json file is present and the fields are correct (there must also be an actual license file at the location that the PackageInfo.json specifies), then the package is a valid package and will function.

However, even though just these two files make a valid package, the package would not serve any useful purpose.  All packages thus also contain their actual payload files (for example, a FindXXXX.CMake file as well as headers and libraries, executables, etc).

An example package folder image on the *authoring* side could be:
``` 
 - PackageInfo.json       <--- required file
 - FindMyLibrary.cmake
 - MyLibrary
   - License.txt          <--- required file, pointed at by PackageInfo.json
   - include
     - MyLibrary
        - mylib.h
   - lib (Directory)
     - windows
       - mylibrary.lib
     - linux
       - mylibrary.a
```
It is convenient to place a Find(LIBRARYNAME).cmake at the root if the package contains libraries or code, because the root of unpacked packages is added to the CMAKE_MODULE_PATH after unpacking (the place where CMake searches for Find*****.cmake files).

## Structure of a package - packaged up
Once you have a package *image* as in the above structure, you use the package build scripts to turn it into a package.  This results in the following files being created (by default in the 'packages' sub-folder).
Note that PackageName comes from PackageInfo.json, not the folder names on disk.

 - PackageName.tar.xz
 - PackageName.tar.xz.SHA256SUMS
 - PackageName.tar.xz.content.SHA256SUMS
 - PackageName.PackageInfo.json

The tar.xz file contains the authored package image (described in the prior section) plus a hash of its contents, named content.SHA256SUMS.

The SHA256SUMS file is the SHA256 sum of the actual tar.xz file.

The content.SHA256SUMS file is a standard SHA256SUMS file that lists each file in the archive and has a SHA256 hash for it.  (Except for the SHA256SUM file itself).  Its the same as the one inside the package tar.xz at the root.

The PackageInfo.json file is just the PackageInfo.json from inside the package.

These four files are whats uploaded to a download site, for the package consumer side to download as needed.

## The package list files
Because package building and uploading is intended to be automated by continuous integration / code review systems, there is a set of package list files which automated systems can use to iterate over all the packages and build/upload them all.

Thus making a package involves creating the above 'package image' folder (either by writing a script to do it or by actually just committing the image to source control) and then also updating the package build list files to mention that folder where the package image now exists.

The package building scripts (discussed later on in this document) expect to be passed a --search-path parameter which tells it where to look for these build list files (usually stored in another folder or repository)

 Given a search path, the scripts will search for files in that path called 
 "package_build_list_host_(windows|linux|darwin).json"(host type specific list).  
 
 Note that the host type in the above name indicates which system the package is being built on, not which system its being built *for*.

The package build list file json file format:
```json
{
    "build_from_source" : {
        "package-name" : "build-script-to-run (params)"
        ... n packages
    },
    "build_from_folder" : { 
        "package-name" : "folder-name"
        ... n packages
    }
}
```

Note that there is a "build_from_source" as well as a "build_from_folder" section.  The above document has so far only covered the "build_from_folder" section (where a pre-made package image folder is already present).  

In the above, "folder-name" is expected to be relative to the search path specified (ie, the location the host files are kept).
In the above, "build-script-to-run" will use the script relative to the search path, so make sure any scripts used are in the same repository or local to the host files.

The working directory for the build script to run will be the folder containing the build script.

"Build from source" is used when, instead of checking in the actual package binaries to source control, you prefer to check in a script that fetches/builds the binaries from elsewhere.  For example, instead of checking in the whole of python pre-compiled, its possible to check in a shell script that will clone the python repo and then build it.   In that case, the script's job is to produce a folder image that is then mentioned later on, again, in the "build_from_folder" section, usually by building, then carefully cherrypicking binaries, headers, etc.   (More on this later on in the document.)

When specifying a *multiplatform* package in a list file, pick **ONE** authoratative host platform to build the package on. For example, if a package contains Windows, Mac, and Linux binaries in it, add the package **ONCE** to either the Linux, Mac, or Windows host files.  By picking one host type for each package, you reduce the combinatorics involved in "What host produced the same package?" versus what it works on (We don't want to end up in a situation where what host a package was built on can cause subtle bugs even for the same logical package).

### Examples
The standard repository contains a few notable examples you can copy from (in the actual package sources repo)
 * The 'xxhash' library is an example of a library that is a header-only (small) library that fits committed directly and thus has no build script, just a package image
 * The 'OpenSSL' library is an example of using the package building system 'vcpkg' to do all the heavy lifting to generate the package image folder.
 * The 'Lua' library is an example of using a 'pull and build from git' script (shipped in that repo) to make it easy to pull, patch, and build from git repositories.

### Package building host notes
Windows is unable to build packages that contain symlinks for Mac and Linux platforms.   It is also unable to build packages that have particular modes on files (such as 'executable' bits set).   If your package contains linux or Mac binaries or symlinks, consider packing those as separate packages, each on its prospective host, or use a symlink and mode aware operating system (Linux or Mac) as the official build host.

## Authoring Scripts
All scripts can be run with --help command line option to see details.

### Script: list_packages.py
This is a development tool which allows you to list the packages that are present in package list files for the current host.  It also validates that the json parse of the package list files are correct and checks for other problems.

### Script: compare_buckets.py
This is a development tool which you give it 2 buckets (usualy a production and development s3 bucket) and it generates information in a table form to help you figure out whats going on in those buckets.  For example, it will tell you what packages do not appear anywhere in the buckets at all, but do appear in the host list files (ie, missing packages).

In general, develop packages in a 'dev' bucket, then promote them to a 'prod' bucket, so this tool can be useful to find out whether promotion has not happened yet.

### Script: build_package.py
This script is the intended entry point into dev testing of their own packages during development.

Example invocation:
```
python3 ./Scripts/build_package.py --search_path ../package-sources zlib-1.2.8.internal
```
It will load the package list files from the given search path, find and verify the information in there for that package, and then build and pack the package into the --search_path sub "packages" subfolder unless you specify --output optional param.

If the package contains build scripts ("build_from_source" in the package list file), it will invoke those build scripts first, allowing them to generate the package image, before attempting to pack the resulting folder.

This script essentially does the 'pack_package' function (see below) but before it does so, does any other building that needs to be done, effectively simulating locally what the build server would do.

### Script: pack_package.py
This is a development tool which allows you to turn any given folder into a package tar.xz and the associated SHASUMS and other files, as well as verify it.  This is only for internal use.

It will not invoke build scripts, its just the 'archiving' part of the pipeline.

This script expects a parameter that points at a folder already containing an authored package image (so with PackageInfo.json, license file, etc).  

The script will verify the package as it builds it (making sure each required file and field is present). After building it, it also unzips it into a temp location and then ensures that the package hashes all match the contents and that no files are extra or missing - it essentially simulates the client user side.

Example invocation:
```
python3 ./Scripts/pack_package.py ./some_folder
```

The result would be a package being placed in ./packages that represents that package.

Note that this script operates at the folder level, and does not require that you update the package list files to function or specify the search path, but you can do so.

### Script: build_all_packages.py

Intended for use in Continuous Integration automation only.

This script loads the package list and then essentially calls build_package.py on those package folders.  

Because it checks to make sure the package isn't already uploaded before trying to build it, you must feed it a semi colon delimited list of package server urls - either on the command line, or in a LY_PACKAGE_SERVER_URLS environment variable.  It will only call the build scripts for packages that are not already available (since packages are immutable).

Example invocation:
```
python3 ./Scripts/build_all_packages.py --server_urls s3://my-package-server;https://cloudfront.cdn.com/mypackages --search_path ../package-sources
```

In general, the scripts are used in a build server - the build_all_packages script is invoked, and then the upload_all_packages script (see below) is invoked afterwards.

Also note - the build_all_packages simulates a client looking for those packages, so it uses the list of server_urls to find them in actual URI format (like s3://blah-bucket-name or https://server_url).  

If you use s3 buckets, your current user profile must be able to access the buckets given.  If you want to use a different AWS profile to access the bucket(s), then set the AWS_PROFILE, or LY_AWS_PROFILE env vars, or pass in the profile on the command line (see --help)

### Script: upload_all_packages.py
This script is intended for automated systems such as a Continuous Integration node.

It iterates over every package it finds in the 'packages' folder (which can be overridden on the command line) and attempts to upload any valid ones to an S3 bucket on AWS.

Note that it operates directly on the package source folder, and not package list files, and thus will attempt to upload **any legitimate packages in that folder**, regardless of whether they were made locally or obtained by some other means.

It will not upload packages that are damaged (it verifies them first) and it will **not upload packages that already exist on the target server** (it won't overwrite them or delete them).

Example invocation:
```
python3 ./Scripts/upload_all_packages.py --bucket_name my-s3-bucket-name
```
Note that unless you override the AWS profile to use (either by AWS_PROFILE, LY_AWS_PROFILE, env var, or by command line option), it will use no profile.  The profile must have write access to that bucket.

Because it writes directly to the bucket using AWS APIs, you must specify a bucket name, not URI or a list of URIs.  so just "my-bucket-name" and **not** "s3://my-bucket-name" or a URI.

Uploading packages requires that the boto3 pip package is installed. (pip install boto3)

## Advanced Topic: Building packages from source
The above section mostly covered how authoring a package works if you already have a pre-built package image.

This way is the easiest way to do it, but comes at a cost - the repository containing all these pre-built binaries can become bloated if every package is uploaded as a pre-built binary.

This is fine for small libraries, but for very large libraries, its better to write a script that *generates* the package image folder by downloading and compiling the source of the package from the official git repository where it lives (and then just supplying the additional required PackageInfo.json and FindXXXX.cmake file).

An example of a package structure when its in "build from source mode" looks like this on the authoring side:

 - PackageInfo.json (same as always)
 - FindMyPackage.cmake (same as always)
 - .gitignore (ignores temp and package folder)
 - build_package_image.py (generates temp and package folder)
 - (any additional files such as patch file)

The "build_package_image.py" file is invoked by the build_all_packages.py script when the folder containing it is in the "build_from_source" section of the json file (see the above section on package list files).  It will be invoked with a working directory of the location of the build_package_image.py file.

Its job is to generate an 'image' of the package folder by any means necessary anywhere it wants to.  This usually means it runs a batch or shell script file which:
 1. makes a 'temp' folder (cleans or deletes)
 2. gets the official source code from a git repository into the temp folder or downloads/unzips a binary release from somewhere.
 3. configures and builds the source code in the temp folder if necessary
 4. makes a 'package' folder
 5. deploys **ONLY** the relevant parts of the built package into the 'package' folder (for example, copy headers, generated lib files, docs, license files, etc)
 6. deploys package system required files into the package folder (for example, copies PackageInfo.json and FindMyPackage.cmake into the package folder)
 7. deletes the temp folder

The result of this script is a folder that basically contains the exact same structure as would have been used in the workflow for a pre-made image of a package.

Then, the same package will be listed again, in the "build from folder" section of the host package list file, except this time, it will list the generated output folder path.

By convention, a package build script will make a sub-folder called 'package' containing the image of the package, but this does not have to be the case.

Current example:  see the python sub-folder.  Note that the python sub-folder is a special case.  The build script is common and located in the python folder - but it detects what host you're on, and will generate hostname/package, not just 'package' (for example linux_x64/package).  This is a good example where the build script produces a package image that isn't just in a 'package' folder, and why you specify a different folder in the 'build_from_source' key to the 'build_from_folder' key.

Thus in the python example, the build script folder is just ./python but the "build_From_folder" section specifies each host's generated sub-platform.  

For example, here is the Darwin file:
```json
    "build_from_source" : {
        "python-3.7.5-darwin" : "python/build_package_image.py (parameters)"
    },
    "build_from_folder" : { 
        "python-3.7.5-darwin" : "python/darwin_x64/package"
    }
}
```
The "build_from_source" entry causes it to run ./python/build_package_image.py
Note that you can specify parameters after the script name.

The "build_from_folder" always executes after build from source, and will cause it to attempt to package up the contents of the ./python/darwin_x64/package folder (which was built using the script).

## Recommended package authoring workflow

 1. Create a sub-folder for your package, and name it (packagename-platform).  Do not use a version number in your package folder name, as updates to the package will be done in the same folder.
 2. Create your PackageInfo.json and FindPackage.cmake
 3. If you're building from source, make your build_package_image.py file and scripts.  Make sure the script creates a 'package' sub-folder and copies the json/cmake files into that folder.  Run the script to generate teh image.
 4. If instead you're just going from a pre-built image, just put the package image in your folder itself and construct it there.

 On the client side, to rapidly iterate
  1. sym-link or copy the package image folder into your package downloaded location (Default is the 3rdParty folder).  Make sure the folder is named after the full package id name in the PackageInfo.json (for example, packagename-version-platform)
  2. Add the ly_associate_package line to the script using it:  ly_associate_package(packagename-version-platform packagename)
  3. use the package (declare its targets a dependency in the usual cmake way)

  Once your rapid iteration is successful, update the json files (package_build_list.json and package_build_list_host_(PLATFORMS).json) to mention your package folder(s) and then test using build_package.ppy.
  
  Once thats done, make a pull request to the repository add your package "sources".

  Once accepted, the package will be uploaded to the 'real' bucket.  You can then remove the sym-link or copy and next time you cmake configure on the client side, it will fetch and use the real package.
