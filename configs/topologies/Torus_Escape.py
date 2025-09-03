from m5.params import *
from m5.objects import *

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology

# Creates a generic Mesh assuming an equal number of cache
# and directory controllers.
# Torus routing is enforced (using link weights)
# to guarantee deadlock freedom.


class Mesh_Torus_Escape(SimpleTopology):
    # This is the topology for torus with escape
    description = "Mesh_Torus"

    def __init__(self, controllers):
        self.nodes = controllers

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes

        num_routers = options.num_cpus
        dimX = options.mesh_rows
        dimZ = options.m_depth

        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_routers)
        assert dimX > 0 and dimX <= num_routers
        assert dimZ > 0 and dimZ <= num_routers
        dimY = int(num_routers / dimX / dimZ / 2)
        assert dimY * dimX * dimZ * 2 == num_routers

        # Create the routers in the mesh
        routers = [
            Router(router_id=i, latency=router_latency)
            for i in range(num_routers)
        ]
        network.routers = routers

        # link counter to set unique link ids
        link_count = 0

        # Add all but the remainder nodes to the list of nodes to be uniformly
        # distributed across the network.
        network_nodes = []
        remainder_nodes = []
        for node_index in range(len(nodes)):
            if node_index < (len(nodes) - remainder):
                network_nodes.append(nodes[node_index])
            else:
                remainder_nodes.append(nodes[node_index])

        # Connect each node to the appropriate router
        ext_links = []
        for (i, n) in enumerate(network_nodes):
            cntrl_level, router_id = divmod(i, num_routers)
            assert cntrl_level < cntrls_per_router
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=n,
                    int_node=routers[router_id],
                    latency=link_latency,
                )
            )
            link_count += 1

        # Connect the remainding nodes to router 0.  These should only be
        # DMA nodes.
        for (i, node) in enumerate(remainder_nodes):
            assert node.type == "DMA_Controller"
            assert i < remainder
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=node,
                    int_node=routers[0],
                    latency=link_latency,
                )
            )
            link_count += 1

        network.ext_links = ext_links

        # Create the mesh links.
        int_links = []

        # For rows, columns and width, we use x,y,z to represent the direction
        # The coordinate (row,col,depth) represents the location of
        # index = depth*dimX*dimY + row*dimY + col
        for row in range(dimX):
            for col in range(dimY):
                for depth in range(dimZ):
                    zdec_out = depth * dimX * dimY + row * dimY + col
                    zinc_in = (
                        ((depth + 1) % dimZ) * dimX * dimY + row * dimY + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[zdec_out],
                            dst_node=routers[zinc_in],
                            src_outport="Up",
                            dst_inport="Down",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[zdec_out + num_routers / 2],
                            dst_node=routers[zinc_in + num_routers / 2],
                            src_outport="Up",
                            dst_inport="Down",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 2

        for row in range(dimX):
            for col in range(dimY):
                for depth in range(dimZ):
                    zdec_in = depth * dimX * dimY + row * dimY + col
                    zinc_out = (
                        ((depth + 1) % dimZ) * dimX * dimY + row * dimY + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[zinc_out],
                            dst_node=routers[zdec_in],
                            src_outport="Down",
                            dst_inport="Up",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[zinc_out + num_routers / 2],
                            dst_node=routers[zdec_in + num_routers / 2],
                            src_outport="Down",
                            dst_inport="Up",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 2

        for row in range(dimX):
            for depth in range(dimZ):
                for col in range(dimY):
                    ydec_out = depth * dimX * dimY + row * dimY + col
                    yinc_in = (
                        depth * dimX * dimY + row * dimY + ((col + 1) % dimY)
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[ydec_out],
                            dst_node=routers[yinc_in],
                            src_outport="North",
                            dst_inport="South",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[ydec_out + num_routers / 2],
                            dst_node=routers[yinc_in + num_routers / 2],
                            src_outport="North",
                            dst_inport="South",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 2

        for row in range(dimX):
            for depth in range(dimZ):
                for col in range(dimY):
                    ydec_in = depth * dimX * dimY + row * dimY + col
                    yinc_out = (
                        depth * dimX * dimY + row * dimY + ((col + 1) % dimY)
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[yinc_out],
                            dst_node=routers[ydec_in],
                            src_outport="South",
                            dst_inport="North",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[yinc_out + num_routers / 2],
                            dst_node=routers[ydec_in + num_routers / 2],
                            src_outport="South",
                            dst_inport="North",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 2

        for col in range(dimY):
            for depth in range(dimZ):
                for row in range(dimX):
                    xdec_out = depth * dimX * dimY + row * dimY + col
                    xinc_in = (
                        depth * dimX * dimY + ((row + 1) % dimX) * dimY + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[xdec_out],
                            dst_node=routers[xinc_in],
                            src_outport="East",
                            dst_inport="West",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[xdec_out + num_routers / 2],
                            dst_node=routers[xinc_in + num_routers / 2],
                            src_outport="East",
                            dst_inport="West",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 2

        for col in range(dimY):
            for depth in range(dimZ):
                for row in range(dimX):
                    xdec_in = depth * dimX * dimY + row * dimY + col
                    xinc_out = (
                        depth * dimX * dimY + ((row + 1) % dimX) * dimY + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[xinc_out],
                            dst_node=routers[xdec_in],
                            src_outport="West",
                            dst_inport="East",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[xinc_out + num_routers / 2],
                            dst_node=routers[xdec_in + num_routers / 2],
                            src_outport="West",
                            dst_inport="East",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 2

        # The links across two toruses
        # Nodes in the main network (id < num_routers/2) are marked as "main",
        # others (id >= num_routers/2) are as "escape"
        # Links are created between routers[id] and routers[id+num_routers/2]
        for router_id in range(num_routers / 2):
            net_in = router_id
            escape_out = router_id + num_routers / 2
            int_links.append(
                IntLink(
                    link_id=link_count,
                    src_node=routers[escape_out],
                    dst_node=routers[net_in],
                    src_outport="Escape",
                    dst_inport="Main",
                    latency=link_latency,
                    weight=1,
                )
            )
            link_count += 1

        for router_id in range(num_routers / 2):
            net_out = router_id
            escape_in = router_id + num_routers / 2
            int_links.append(
                IntLink(
                    link_id=link_count,
                    src_node=routers[net_out],
                    dst_node=routers[escape_in],
                    src_outport="Main",
                    dst_inport="Escape",
                    latency=link_latency,
                    weight=1,
                )
            )
            link_count += 1

        network.int_links = int_links

    # Register nodes with filesystem
    def registerTopology(self, options):
        for i in range(options.num_cpus):
            FileSystemConfig.register_node(
                [i], MemorySize(options.mem_size) // options.num_cpus, i
            )
