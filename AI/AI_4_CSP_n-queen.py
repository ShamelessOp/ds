def print_board(board):
    for row in board:
        print(" ".join("Q" if col else "." for col in row))
    print("\n")


# ---------------- BACKTRACKING ----------------
def is_safe(board, row, col, n):
    # Check column
    for i in range(row):
        if board[i][col]:
            return False

    # Check left diagonal
    for i, j in zip(range(row, -1, -1), range(col, -1, -1)):
        if board[i][j]:
            return False

    # Check right diagonal
    for i, j in zip(range(row, -1, -1), range(col, n)):
        if board[i][j]:
            return False

    return True


def solve_n_queens_backtracking(board, row, n):
    if row == n:
        print_board(board)
        return True   # Stop after first solution

    for col in range(n):
        if is_safe(board, row, col, n):
            board[row][col] = True

            if solve_n_queens_backtracking(board, row + 1, n):
                return True

            board[row][col] = False  # Backtrack

    return False


def n_queens_backtracking(n):
    board = [[False] * n for _ in range(n)]
    if not solve_n_queens_backtracking(board, 0, n):
        print("No solution exists.")


# ---------------- BRANCH & BOUND ----------------
def is_safe_branch_and_bound(row, col, cols, diags1, diags2, n):
    return not (cols[col] or diags1[row + col] or diags2[row - col + (n - 1)])


def solve_n_queens_branch_and_bound(row, n, cols, diags1, diags2, board):
    if row == n:
        print_board(board)
        return True

    for col in range(n):
        if is_safe_branch_and_bound(row, col, cols, diags1, diags2, n):
            board[row][col] = True
            cols[col] = True
            diags1[row + col] = True
            diags2[row - col + (n - 1)] = True

            if solve_n_queens_branch_and_bound(row + 1, n, cols, diags1, diags2, board):
                return True

            # Backtrack
            board[row][col] = False
            cols[col] = False
            diags1[row + col] = False
            diags2[row - col + (n - 1)] = False

    return False


def n_queens_branch_and_bound(n):
    board = [[False] * n for _ in range(n)]
    cols = [False] * n
    diags1 = [False] * (2 * n - 1)
    diags2 = [False] * (2 * n - 1)

    if not solve_n_queens_branch_and_bound(0, n, cols, diags1, diags2, board):
        print("No solution exists.")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    n = 8

    print("Backtracking Solution:")
    n_queens_backtracking(n)

    print("\nBranch and Bound Solution:")
    n_queens_branch_and_bound(n)