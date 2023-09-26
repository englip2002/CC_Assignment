x = ((1, '2022 July', '2023 January - 2023 July', 0), (2, '2022 November', '2023 May - 2023 November', 0), (3, '2023 January', '2024 July - 2025 January', 0))

a, b = [(i[1], i[2]) for i in x if i[0] == 1][0]

print(a)
print(b)