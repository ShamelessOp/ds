import heapq

class AStar:
    def __init__(self, grid, start, goal):
        self.grid = grid              # 2D grid (0 = free, 1 = blocked)
        self.start = start
        self.goal = goal
        self.rows = len(grid)
        self.cols = len(grid[0])

    def heuristic(self, node):
        # Manhattan Distance
        return abs(node[0] - self.goal[0]) + abs(node[1] - self.goal[1])

    def neighbors(self, node):
        # Right, Down, Left, Up
        dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        result = []

        for d in dirs:
            neighbor = (node[0] + d[0], node[1] + d[1])

            if (0 <= neighbor[0] < self.rows and
                0 <= neighbor[1] < self.cols and
                self.grid[neighbor[0]][neighbor[1]] == 0):
                result.append(neighbor)

        return result

    def a_star_search(self):
        open_list = []
        heapq.heappush(open_list, (0, self.start))

        came_from = {}
        g_score = {self.start: 0}
        f_score = {self.start: self.heuristic(self.start)}

        while open_list:
            current = heapq.heappop(open_list)[1]

            if current == self.goal:
                return self.reconstruct_path(came_from, current)

            for neighbor in self.neighbors(current):
                tentative_g_score = g_score[current] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor)

                    heapq.heappush(open_list, (f_score[neighbor], neighbor))

        return []  # No path found

    def reconstruct_path(self, came_from, current):
        total_path = [current]

        while current in came_from:
            current = came_from[current]
            total_path.append(current)

        return total_path[::-1]


# Grid (Solvable)
grid = [
    [0, 1, 0, 1, 0],
    [0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [1, 1, 0, 1, 0],
    [0, 0, 0, 0, 0],
]

start = (0, 2)
goal = (4, 0)

a_star = AStar(grid, start, goal)
path = a_star.a_star_search()

print("Path from start to goal:", path)