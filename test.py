# field = [
#     [1, 1, 0, 0, 1],
#     [0, 0, 1, 0, 1],
#     [1, 0, 0, 1, 0],
#     [0, 1, 0, 1, 0],
#     [1, 0, 1, 0, 0],
# ]

# pos = [0, 0]
# actions = ['upLeft', 'up', 'upRight', 'left', 'center', 'right', 'downLeft', 'down', 'downRight']

# solutionPath = []

# def isGoal(thisPos):
#     return thisPos[0] == len(field) - 1

# def findSafeSpaces(thisPos):
#     output = []
#     for i, a in enumerate(actions):
#         tempPos = [-1 + (i % 3) + thisPos[0], -1 + int((i) / 3) + thisPos[1]]
#         if (tempPos[0] >= 0 and tempPos[0] < len(field) and tempPos[1] >= 0 and tempPos[1] < len(field[0])):
#             output.append({'action': a, 'pos': tempPos})
#     return output

# while (not isGoal(pos)):
#     safeSpaces = findSafeSpaces
#     for each in safeSpaces:
#         ...
# print(findSafeSpaces([0,0]))

x = ()
print(type(x))