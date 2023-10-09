import glob
import sys
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class Function:
    name: str
    parameters: str
    return_type: str | None
    def __init__(self, name: str, parameters: str, return_type: str):
        self.name = name.strip()
        self.parameters = (re.sub(r" +", "", parameters.replace("\n", ""))
                           .replace(",)", ")")
                           .replace(":", ": ")
                           .replace(",", ", ")
                           .strip())
        self.return_type = return_type.strip() if return_type else None


@dataclass
class Module:
    name: str | None
    functions: list[Function]


def parse_file(path: Path) -> Module:
    mod_name: str = path.parent if path.name == "mod.rs" else path.name.removesuffix(".rs")
    str_data: str = path.open("r").read()
    regex: re.Pattern[str] = re.compile(r"pub fn\s+([\w_]+)\s*(\(.*?\))\s*(?:->\s*([\w_:<>\[\](), &']+))?\s+?{", re.DOTALL|re.MULTILINE)
    functions = [Function(*fn.groups()) for fn in regex.finditer(str_data)]
    return Module(mod_name, functions)


if __name__ == "__main__":
    dirname = sys.argv[1]
    traitname = sys.argv[2]

    modules = [parse_file(Path(filename)) for filename in glob.glob(f"{dirname}/src/**.rs")]
    trait = ["pub trait "+traitname+" {"]
    for m in modules:
        for f in m.functions:
            rettype = f" -> {f.return_type}" if f.return_type else ""
            trait.append(f"    fn {f.name}{f.parameters}{rettype};")
    trait.append("}")

    impl = ["impl "+traitname+" for NameMe {"]

    for m in modules:
        prefix = f"{m.name}::" if m.name else ""
        for f in m.functions:
            rettype = f" -> {f.return_type}" if f.return_type else ""
            param_names = [p.split(":")[0] for p in f.parameters.replace("(", "").split(",") if ":" in p]
            call_params = f"({','.join(param_names)})"
            impl.append(f"    fn {f.name}{f.parameters}{rettype}")
            impl.append("    {")
            impl.append(f"        {prefix}{f.name}{call_params}")
            impl.append("    }")
    impl.append("}")

    print("\n".join(trait))
    print("\n".join(impl))
