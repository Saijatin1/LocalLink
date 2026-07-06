from app.models.routing_node import RoutingNode
from app.utils.geo import distance_between


class DistanceMatrixBuilder:

    @staticmethod
    def build(
        nodes: list[RoutingNode],
    ) -> list[list[int]]:

        matrix = []

        for source in nodes:

            row = []

            for destination in nodes:

                row.append(
                    distance_between(
                        source.location,
                        destination.location,
                    )
                )

            matrix.append(row)

        return matrix