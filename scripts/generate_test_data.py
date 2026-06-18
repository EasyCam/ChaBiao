"""Generate a realistic ~1MB test spreadsheet with many rows for ChaBiao testing."""

import random
import sys
from pathlib import Path

import pandas as pd
import numpy as np


def generate_test_data(output_path: str = "test_data_large.xlsx", rows: int = 50000):
    random.seed(42)
    np.random.seed(42)

    cities = [
        "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou",
        "Chengdu", "Wuhan", "Nanjing", "Xi'an", "Chongqing",
        "Suzhou", "Tianjin", "Changsha", "Zhengzhou", "Dongguan",
        "Qingdao", "Dalian", "Kunming", "Xiamen", "Fuzhou",
    ]
    departments = [
        "Engineering", "Sales", "Marketing", "Finance",
        "HR", "Operations", "Legal", "Support",
        "Research", "Management",
    ]
    levels = list(range(1, 11))
    statuses = ["Active", "On Leave", "Probation", "Transferred", "Retired"]
    projects = [f"PRJ-{i:04d}" for i in range(1, 501)]
    skills = [
        "Python", "Java", "C++", "JavaScript", "Go",
        "Rust", "SQL", "React", "Vue", "Docker",
        "Kubernetes", "AWS", "Azure", "GCP", "Linux",
    ]
    products = [
        "Widget A", "Widget B", "Gadget X", "Gadget Y",
        "Tool M", "Tool N", "Part S", "Part T",
        "Component P", "Component Q",
    ]

    data = {
        "ID": range(1, rows + 1),
        "Name": [f"Employee_{i:06d}" for i in range(1, rows + 1)],
        "English_Name": [
            f"{random.choice(['A','B','C','D','E','F','G','H','J','K'])}"
            f"{random.choice(['a','b','c','d','e','f','g','h','i','j'])}"
            f"{random.choice(['m','n','p','r','s','t','w','x','y','z'])}"
            for _ in range(rows)
        ],
        "City": [random.choice(cities) for _ in range(rows)],
        "Department": [random.choice(departments) for _ in range(rows)],
        "Level": [random.choice(levels) for _ in range(rows)],
        "Salary": np.random.randint(25000, 200000, rows).tolist(),
        "Bonus": np.random.randint(0, 50000, rows).tolist(),
        "Age": np.random.randint(22, 62, rows).tolist(),
        "Score": np.round(np.random.uniform(0, 100, rows), 2).tolist(),
        "Performance": np.round(np.random.uniform(0, 5, rows), 2).tolist(),
        "Status": [random.choice(statuses) for _ in range(rows)],
        "Project": [random.choice(projects) for _ in range(rows)],
        "Skill": [random.choice(skills) for _ in range(rows)],
        "Product": [random.choice(products) for _ in range(rows)],
        "Sales_Amount": np.round(np.random.uniform(100, 99999, rows), 2).tolist(),
        "Cost": np.round(np.random.uniform(50, 50000, rows), 2).tolist(),
        "Email": [f"user{i:06d}@example.com" for i in range(1, rows + 1)],
        "Phone": [f"1{random.randint(30,99)}{random.randint(10000000,99999999)}" for _ in range(rows)],
        "Address": [f"No.{random.randint(1,999)} {random.choice(['Main','Park','Lake','River','Hill'])} St" for _ in range(rows)],
        "Join_Date": pd.date_range("2010-01-01", periods=rows, freq="6h").strftime("%Y-%m-%d").tolist(),
    }

    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False, engine="openpyxl")
    size_mb = Path(output_path).stat().st_size / 1024 / 1024
    print(f"Generated: {output_path}")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Columns: {list(df.columns)}")

    csv_path = output_path.replace(".xlsx", ".csv")
    df.to_csv(csv_path, index=False)
    csv_size = Path(csv_path).stat().st_size / 1024 / 1024
    print(f"\nAlso generated: {csv_path}")
    print(f"  Size: {csv_size:.1f} MB")


if __name__ == "__main__":
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    output = sys.argv[2] if len(sys.argv) > 2 else "test_data_large.xlsx"
    generate_test_data(output, rows)