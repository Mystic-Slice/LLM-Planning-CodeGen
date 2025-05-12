from grasp.util import load_jsonl

grids = [
("outer_upDown_free", 99),
("outer_leftRight_free", 61),
("inner_upDown_block", 45),
]

for (dataset_name, idx) in grids:
    dataset_file = f"GRASP\data\grids\{dataset_name}.jsonl"

    data = load_jsonl(dataset_file)

    print(data[idx]['grid'])
    print("---------")

    