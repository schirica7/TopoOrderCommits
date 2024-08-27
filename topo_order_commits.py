#!/usr/bin/env python3

# Recommended libraries. Not all of them may be needed.
import os, sys, zlib
from collections import deque

# Note: This is the class for a doubly linked list. Some implementations of
# this assignment only require the `self.parents` field. Delete the
# `self.children` field if you don't think its necessary.
class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = list[CommitNode]()
        self.children = list[CommitNode]()

# ============================================================================
# ======================== Auxiliary Functions ===============================
# ============================================================================

def create_head_to_branches(branch_list: list[(str, str)]) -> dict[str, list[str]]:
    head_to_branches = dict[str, list[str]]()

    for item in branch_list:
        if item[1] not in head_to_branches:
            head_to_branches[item[1]] = list[str]()

        head_to_branches[item[1]].append(item[0])
    
    return head_to_branches
# ============================================================================
# =================== Part 1: Discover the .git directory ====================
# ============================================================================

def get_git_directory() -> str:
    """
    :rtype: bool

    Checks if `topo_order_commits.py` is inside a Git repository.
    """
    while not os.path.exists(os.getcwd() + "/.git"):
        if os.getcwd() == "/":
            return "N/A"

        os.chdir(os.path.dirname(os.getcwd()))
    
    s = os.getcwd() + "/.git"
    return (s)


# ============================================================================ 
# =================== Part 2: Get the list of local branch names =============
# ============================================================================

def get_branches(path : str) -> list[(str, str)]:
    """
    :type path: str
    :rtype: list[(str, str)]

    Returns a list of tuples of branch names and the commit hash
    of the head of the branch.
    """
    commit_list = list[(str, str)]()

    heads_path = path + "/refs/heads"
    os.chdir(heads_path)

    for root, dirpath, filenames in os.walk(os.getcwd()):
        for filename in filenames:
            file_path = os.path.join(root, filename)

            if (os.path.isfile(file_path)):
                f = open(file_path, 'r')
                commit_list.append(tuple([os.path.relpath(file_path, heads_path), f.read().strip()]))
                f.close()

    return commit_list


# ============================================================================
# =================== Part 3: Build the commit graph =========================
# ============================================================================

def build_commit_graph(branches_list : list[(str, str)]) -> dict[str, CommitNode]:
    """
    :type branches_list: list[(str, str)]
    :rtype: dict[str, CommitNode]

    Iterative builds the commit graph from the list of branches and
    returns a dictionary mapping commit hashes to commit nodes.
    """
    os.chdir( get_git_directory() + "/objects")

    hash_dict = dict[str, CommitNode]()
    commits_list = [branch[1] for branch in branches_list]
    visited_hashes = set()

    while commits_list:
        hash = commits_list.pop()

        if hash in visited_hashes:
            continue

        visited_hashes.add(hash)

        if hash not in hash_dict:
            hash_dict[hash] = CommitNode(hash)
        
        cur_hash = hash_dict[hash]
        commitPath = "./" + hash[0:2] + "/" + hash[2:]

        with open(commitPath, 'rb') as file:
            compressed_data = file.read()
            decompressed_data = zlib.decompress(compressed_data)
            decompressed_data_string = decompressed_data.decode()

            data_list = decompressed_data_string.split("\n")
            parent_hashes = list[str]()

            for item in data_list:
                if item[:6] == 'parent':
                    #sys.stdout.write(item + "\n")
                    parent_hashes.append(item[7:])
            parent_hashes.sort()

            for parent in parent_hashes:
                if parent not in visited_hashes:
                    commits_list.append(parent)
                    
                if parent not in hash_dict:
                    hash_dict[parent] = CommitNode(parent)
                    
                cur_hash.parents.append(hash_dict[parent])
                hash_dict[parent].children.append(cur_hash)
    return hash_dict

# ============================================================================
# ========= Part 4: Generate a topological ordering of the commits ===========
# ============================================================================

def topo_sort(hash_dict : dict[str, CommitNode]) -> list[str]:
    """
    :type hash_dict: dict[str, CommitNode]
    :rtype: list[str]

    Generates a topological ordering of the commits in the commit graph.
    The topological ordering is represented as a list of commit hashes. See
    the LA Worksheet for some starter code for Khan's algorithm.

    - More-or-less used the code for CS classes on the LA worksheet.
    """
    #This used to be passed in a list of root commits. I'm now creating that list of root commits here.
    #Create a queue of root commits. 
    root_commits = deque()
    visited_parents = set()

    for node in hash_dict:
        if not hash_dict[node].parents:
            root_commits.append(node)
            
    sorted_commits = list[str]()
    
    while root_commits:
        n = root_commits.popleft()
        sorted_commits.append(n)

        for i in hash_dict[n].children[:]:
            visited_parents.add(n)

            all_parents_visited = True
            for parent in hash_dict[i.commit_hash].parents:
                if parent.commit_hash not in visited_parents:
                    all_parents_visited = False
                    break
            
            if all_parents_visited:
                root_commits.append(i.commit_hash)
    
    sorted_commits.reverse()
    return sorted_commits


# ============================================================================
# ===================== Part 5: Print the commit hashes ======================
# ============================================================================

def ordered_print(
    commit_nodes : dict[str, CommitNode],
    topo_ordered_commits : list[str],
    head_to_branches : dict[str, list[str]]
):
    # jumped initialized to false
    # for every commit
    #     if we are doing a jump we should print a stick hash
    #         the next print is not a jump
    #         print the children of the current commit started with a “=”
        
    #     print the current commit hash followed by the branches
        
    #     if the next commit in topo_order_commits is not a parent of the current commit
    #         we are doing a jump
    #         print the parents of the current commit followed by a “=”
    jumped = False

    for (index, commit) in enumerate(topo_ordered_commits):
        # Sticky start
        if jumped:
            jumped = False

            sorted_child_hashes = []

            for child in commit_nodes[commit].children:
                sorted_child_hashes.append(child.commit_hash)

            sorted_child_hashes.sort()
            sys.stdout.write("=" + " ".join(sorted_child_hashes) + "\n")
        
        # Normal printing
        sys.stdout.write(commit)

        if head_to_branches.get(commit):
            for branch in sorted(head_to_branches[commit]):
                sys.stdout.write(" " + branch)
            
        sys.stdout.write("\n")

        #Sticky end
        if index < (len(topo_ordered_commits) - 1):
            if commit_nodes[topo_ordered_commits[index + 1]] not in commit_nodes[commit].parents:
                jumped = True
                sys.stdout.write(" ".join([parent.commit_hash for parent in commit_nodes[commit].parents]) + "=\n\n")


# ============================================================================
# ==================== Topologically Order Commits ===========================
# ============================================================================

def topo_order_commits():
    """
    Combines everything together.
    """
    # Check if you are inside a Git repository.
    # Part 1: Discover the .git directory.
    path = get_git_directory()
    if path == "N/A":
        sys.stderr.write("Not inside a Git repository\n")
        exit(1)
    
    # Part 2: Get the list of local branch names.
    branch_list = get_branches(path)

    # Part 3: Build the commit graph
    graph = build_commit_graph(branch_list)

    # Part 4: Generate a topological ordering of the commits in the graph, using root commit nodes.
    ordered_commits = topo_sort(graph)
    
    # Generate the head_to_branches dictionary showing which
    # branches correspond to each head commit

    head_to_branches = create_head_to_branches(branch_list)

    # Part 5: Print the commit hashes in the topological order.
    ordered_print(graph, ordered_commits, head_to_branches)
# ============================================== ==============================

if __name__ == '__main__':
    topo_order_commits()