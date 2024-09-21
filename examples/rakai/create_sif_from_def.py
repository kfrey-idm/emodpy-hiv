#!/usr/bin/env python

from idmtools.core.platform_factory import Platform
from idmtools_platform_comps.utils.singularity_build import SingularityBuildWorkItem

if __name__ == '__main__':
    platform = Platform("CALCULON")
    sbi = SingularityBuildWorkItem(name="Create ubuntu sif with def file", definition_file="centos.def", image_name="dtk_centos.sif")
    sbi.tags = dict(ubuntu="20.04")
    sbi.run(wait_until_done=True, platform=platform)
    if sbi.succeeded:
        # Write ID file
        sbi.asset_collection.to_id_file("dtk_centos.id")
