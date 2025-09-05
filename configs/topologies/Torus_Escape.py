# -*- coding: utf-8 -*-
# Torus_Escape.py
# 3D Torus topology with escape VC support for gem5 v23
# No vnet_list, compatible with Garnet_standalone

from m5.params import *
from m5.objects import *

from common import FileSystemConfig
from topologies.BaseTopology import SimpleTopology
import math

# Helper functions for coordinate <-> router ID
def coordToId(x, y, z, dimX, dimY, dimZ):
    return z * (dimX * dimY) + y * dimX + x

def idToCoord(rid, dimX, dimY, dimZ):
    z = rid // (dimX * dimY)
    y = (rid % (dimX * dimY)) // dimX
    x = (rid % (dimX * dimY)) % dimX
    return (x, y, z)


class Torus_Escape(SimpleTopology):
    description='3D Torus with escape routing'

    def __init__(self, controllers):
        self.nodes = controllers

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        num_routers = options.num_cpus
        dimX = options.mesh_rows
        dimZ = options.mesh_depth
        dimY = num_routers // (dimX * dimZ)
        assert dimX * dimY * dimZ == num_routers, "num_routers must equal dimX*dimY*dimZ"

        link_latency = options.link_latency
        router_latency = options.router_latency

        # Create routers
        routers = [Router(router_id=i, latency=router_latency) for i in range(num_routers)]
        network.routers = routers

        # External links
        ext_links = []
        link_count = 0
        for i, node in enumerate(nodes):
            router_id = i % num_routers
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=node,
                    int_node=routers[router_id],
                    latency=link_latency
                )
            )
            link_count += 1
        network.ext_links = ext_links

        # Internal links (3D torus)
        int_links = []
        for z in range(dimZ):
            for y in range(dimY):
                for x in range(dimX):
                    src = coordToId(x, y, z, dimX, dimY, dimZ)
                    # X dimension
                    dst = coordToId((x + 1) % dimX, y, z, dimX, dimY, dimZ)
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[src],
                                             dst_node=routers[dst],
                                             src_outport="East",
                                             dst_inport="West",
                                             latency=link_latency))
                    link_count += 1
                    dst = coordToId((x - 1 + dimX) % dimX, y, z, dimX, dimY, dimZ)
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[src],
                                             dst_node=routers[dst],
                                             src_outport="West",
                                             dst_inport="East",
                                             latency=link_latency))
                    link_count += 1

                    # Y dimension
                    dst = coordToId(x, (y + 1) % dimY, z, dimX, dimY, dimZ)
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[src],
                                             dst_node=routers[dst],
                                             src_outport="North",
                                             dst_inport="South",
                                             latency=link_latency))
                    link_count += 1
                    dst = coordToId(x, (y - 1 + dimY) % dimY, z, dimX, dimY, dimZ)
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[src],
                                             dst_node=routers[dst],
                                             src_outport="South",
                                             dst_inport="North",
                                             latency=link_latency))
                    link_count += 1

                    # Z dimension
                    dst = coordToId(x, y, (z + 1) % dimZ, dimX, dimY, dimZ)
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[src],
                                             dst_node=routers[dst],
                                             src_outport="Up",
                                             dst_inport="Down",
                                             latency=link_latency))
                    link_count += 1
                    dst = coordToId(x, y, (z - 1 + dimZ) % dimZ, dimX, dimY, dimZ)
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[src],
                                             dst_node=routers[dst],
                                             src_outport="Down",
                                             dst_inport="Up",
                                             latency=link_latency))
                    link_count += 1

        network.int_links = int_links

    # Register nodes with filesystem
    def registerTopology(self, options):
        for i in range(options.num_cpus):
            FileSystemConfig.register_node([i],
                                           MemorySize(options.mem_size)//options.num_cpus,
                                           i)
