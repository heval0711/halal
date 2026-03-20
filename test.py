import random


random_list = [i for i in range(1, 16)]
random.shuffle(random_list)

print(f"{random_list = }")

sample = sorted(random.sample(random_list, 10))
choices = sorted(random.choices(random_list, k=10))

print(f"{sample = }")
print(f"{choices = }")
