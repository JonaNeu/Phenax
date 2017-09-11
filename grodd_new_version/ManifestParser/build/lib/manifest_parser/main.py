#!/usr/bin/env python3

import argparse

from manifest_parser.manifest import Manifest

DESCRIPTION = "Get some infos from Android APK manifests."


def main():
    parser = argparse.ArgumentParser(description = DESCRIPTION)
    parser.add_argument("manifest_path", type = str,
                        help = "path to a manifest file")
    args = parser.parse_args()

    manifest = Manifest(args.manifest_path)
    manifest.print_info()


if __name__ == "__main__":
    main()