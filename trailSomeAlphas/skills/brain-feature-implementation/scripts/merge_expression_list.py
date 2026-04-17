import json
import argparse
from pathlib import Path
import sys

def load_data_dir(dataset_name=None):
    script_dir = Path(__file__).resolve().parent
    workspace_dir = script_dir.parent
    
    if not dataset_name:
        data_root = workspace_dir / "data"
        if not data_root.exists():
            print("Error: Data directory not found.", file=sys.stderr)
            sys.exit(1)
            
        subdirs = [d for d in data_root.iterdir() if d.is_dir()]
        
        if len(subdirs) == 1:
            dataset_name = subdirs[0].name
            print(f"Auto-detected dataset: {dataset_name}", file=sys.stderr)
            return workspace_dir / "data" / dataset_name
        elif len(subdirs) > 1:
            print("Error: Multiple datasets found. Please specify --dataset.", file=sys.stderr)
            sys.exit(1)
        else:
            print("Error: No dataset folders found inside data directory.", file=sys.stderr)
            sys.exit(1)

    return workspace_dir / "data" / dataset_name

def main():
    parser = argparse.ArgumentParser(description="Merge all generated expressions from idea JSON files.")
    parser.add_argument("--dataset", help="Name of the dataset folder containing idea JSONs.")
    parser.add_argument("--output", default="final_expressions.json", help="Output filename.")
    
    args = parser.parse_args()
    
    dataset_dir = load_data_dir(args.dataset)
    
    if not dataset_dir.exists():
        print(f"Error: Dataset directory {dataset_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
        
    all_expressions = []
    
    # Find all idea json files (supports idea_*.json and *_idea_*.json)
    json_files = list(dataset_dir.glob("idea_*.json"))
    if not json_files:
        json_files = list(dataset_dir.glob("*_idea_*.json"))
    
    if not json_files:
        print(f"No idea_*.json files found in {dataset_dir}", file=sys.stderr)
        sys.exit(0)
        
    print(f"Found {len(json_files)} idea files. Merging...")
    
    for jf in json_files:
        try:
            with open(jf, 'r') as f:
                data = json.load(f)
                exprs = data.get("expression_list", [])
                if exprs:
                    all_expressions.extend(exprs)
                    print(f"  + {jf.name}: {len(exprs)} expressions")
                else:
                    print(f"  - {jf.name}: 0 expressions")
        except Exception as e:
            print(f"  ! Error reading {jf.name}: {e}", file=sys.stderr)
            
    # Remove duplicates if desired? Usually we keep them or set them. 
    # Let's make unique to be safe, but preserve order as best as possible.
    unique_expressions = []
    seen = set()
    for ex in all_expressions:
        if ex not in seen:
            unique_expressions.append(ex)
            seen.add(ex)
            
    output_path = dataset_dir / args.output
    
    try:
        with open(output_path, 'w') as f:
            json.dump(unique_expressions, f, indent=4)
        print(f"\nSuccessfully merged {len(unique_expressions)} unique expressions.")
        print(f"Output saved to: {output_path}")
    except Exception as e:
        print(f"Error saving output: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
