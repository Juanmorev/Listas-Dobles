import unittest

from core.doubly_linked_list import DoublyLinkedList
from models.station import Station
from services.route import Route
from services.train import Direction, Train


def names(route):
    return [s.name for s in route.stations]


def rev_names(route):
    return [s.name for s in reversed(route.stations)]


class DoublyLinkedListTests(unittest.TestCase):
    def build(self, values):
        dll = DoublyLinkedList()
        for v in values:
            dll.append(v)
        return dll

    def assert_consistent(self, dll):
        self.assertEqual(list(dll), list(reversed(list(reversed(dll)))))
        self.assertEqual(len(list(dll)), len(dll))
        if dll.head:
            self.assertIsNone(dll.head.prev)
            self.assertIsNone(dll.tail.next)

    def test_append_prepend_insert(self):
        dll = self.build([1, 2, 3])
        dll.prepend(0)
        dll.insert(2, 99)
        dll.insert(50, 7)
        self.assertEqual(list(dll), [0, 1, 99, 2, 3, 7])
        self.assertEqual(list(reversed(dll)), [7, 3, 2, 99, 1, 0])
        self.assert_consistent(dll)

    def test_remove(self):
        dll = self.build([1, 2, 3, 4])
        dll.remove_at(0)
        dll.remove_at(2)
        dll.remove_at(0)
        self.assertEqual(list(dll), [3])
        dll.remove_at(0)
        self.assertTrue(dll.is_empty())
        self.assertIsNone(dll.head)
        self.assertIsNone(dll.tail)

    def test_node_at_from_both_ends(self):
        dll = self.build(list(range(10)))
        for i in range(10):
            self.assertEqual(dll.node_at(i).value, i)
        with self.assertRaises(IndexError):
            dll.node_at(10)

    def test_reverse_and_move(self):
        dll = self.build([1, 2, 3, 4])
        dll.reverse()
        self.assertEqual(list(dll), [4, 3, 2, 1])
        self.assertEqual(list(reversed(dll)), [1, 2, 3, 4])
        dll.move(0, 3)
        self.assertEqual(list(dll), [3, 2, 1, 4])
        self.assert_consistent(dll)


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.route = Route()
        for n in "ABCDE":
            self.route.add_station(Station(n, stop_minutes=1))

    def test_duplicate_name(self):
        with self.assertRaises(ValueError):
            self.route.add_station(Station("a"))

    def test_positions(self):
        self.route.add_station(Station("S"), "start")
        self.route.add_station(Station("M"), 3)
        self.assertEqual(names(self.route), list("SABMCDE"))
        self.assertEqual(rev_names(self.route), list("EDCMBAS"))

    def test_plan_trip_both_directions(self):
        nodes = list(self.route.stations.nodes())
        fwd = self.route.plan_trip(nodes[0], nodes[3])
        self.assertEqual(fwd.direction, "forward")
        self.assertEqual([n.value.name for n in fwd.stops], list("ABCD"))
        self.assertEqual(fwd.minutes, 3 * 2 + 2)
        back = self.route.plan_trip(nodes[4], nodes[1])
        self.assertEqual(back.direction, "backward")
        self.assertEqual([n.value.name for n in back.stops], list("EDCB"))

    def test_move_and_reverse(self):
        node = self.route.stations.node_at(1)
        self.assertTrue(self.route.move_station(node, 2))
        self.assertEqual(names(self.route), list("ACDBE"))
        self.assertFalse(self.route.move_station(self.route.stations.head, -1))
        self.route.reverse()
        self.assertEqual(names(self.route), list("EBDCA"))


class TrainTests(unittest.TestCase):
    def test_bounces_at_terminals(self):
        route = Route()
        for n in "ABC":
            route.add_station(Station(n))
        train = Train(route)
        visited = [train.step().value.name for _ in range(6)]
        self.assertEqual(visited, list("ABCBAB"))
        self.assertIs(train.direction, Direction.FORWARD)

    def test_release_on_removal(self):
        route = Route()
        nodes = [route.add_station(Station(n)) for n in "ABC"]
        train = Train(route)
        train.place_at(nodes[1])
        train.release(nodes[1])
        self.assertIs(train.position, nodes[2])


if __name__ == "__main__":
    unittest.main()
