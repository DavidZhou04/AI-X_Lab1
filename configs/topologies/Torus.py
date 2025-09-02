from m5.params import *
from m5.objects import *

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology

# Creates a generic Mesh assuming an equal number of cache
# and directory controllers.
# XY routing is enforced (using link weights)
# to guarantee deadlock freedom.


class Mesh_XY(SimpleTopology):
    description = "Mesh_XY"

    def __init__(self, controllers):
        self.nodes = controllers

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes

        num_routers = options.num_cpus
        num_rows = options.mesh_rows
        mesh_depth = options.mesh_depth

        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_routers)
        assert num_rows > 0 and num_rows <= num_routers
        assert mesh_depth > 0 and mesh_depth <= num_routers
        num_columns = int(num_routers / num_rows / mesh_depth)
        assert num_columns * num_rows * mesh_depth == num_routers

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

        # TODO:internal links in 3D torus
        # For rows, columns and width, we use x,y,z to represent the direction
        # The coordinate (row,col,depth) represents the location of
        # index = depth*num_rows*num_columns + row*num_columns + col
        for row in range(num_rows):
            for col in range(num_columns):
                for depth in range(mesh_depth):
                    zdec_out = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    zinc_in = (
                        ((depth + 1) % mesh_depth) * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[zdec_out],
                            dst_node=routers[zinc_in],
                            src_outport="zDec",
                            dst_inport="zInc",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        for row in range(num_rows):
            for col in range(num_columns):
                for depth in range(mesh_depth):
                    zdec_in = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    zinc_out = (
                        ((depth + 1) % mesh_depth) * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[zinc_out],
                            dst_node=routers[zdec_in],
                            src_outport="zInc",
                            dst_inport="zDec",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        for row in range(num_rows):
            for depth in range(mesh_depth):
                for col in range(num_columns):
                    ydec_out = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    yinc_in = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + ((col + 1) % num_columns)
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[ydec_out],
                            dst_node=routers[yinc_in],
                            src_outport="yDec",
                            dst_inport="yInc",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        for row in range(num_rows):
            for depth in range(mesh_depth):
                for col in range(num_columns):
                    ydec_in = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    yinc_out = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + ((col + 1) % num_columns)
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[yinc_out],
                            dst_node=routers[ydec_in],
                            src_outport="yInc",
                            dst_inport="yDec",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        for col in range(num_columns):
            for depth in range(mesh_depth):
                for row in range(num_rows):
                    xdec_out = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    xinc_in = (
                        depth * num_rows * num_columns
                        + ((row + 1) % num_rows) * num_columns
                        + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[xdec_out],
                            dst_node=routers[xinc_in],
                            src_outport="xDec",
                            dst_inport="xInc",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        for col in range(num_columns):
            for depth in range(mesh_depth):
                for row in range(num_rows):
                    xdec_in = (
                        depth * num_rows * num_columns
                        + row * num_columns
                        + col
                    )
                    xinc_out = (
                        depth * num_rows * num_columns
                        + ((row + 1) % num_rows) * num_columns
                        + col
                    )
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[xinc_out],
                            dst_node=routers[xdec_in],
                            src_outport="xInc",
                            dst_inport="xDec",
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
