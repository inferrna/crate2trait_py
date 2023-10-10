import glob
import sys
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class Function:
    async_pref: str | None
    name: str
    parameters: str
    return_type: str | None
    def __init__(self, async_pref:str|None,  name: str, parameters: str, return_type: str|None):
        self.async_pref = async_pref.strip() if async_pref else None
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
    print(f"Parsing {path}")
    mod_name: str = path.parent if path.name == "mod.rs" else path.name.removesuffix(".rs")
    str_data: str = path.open("r").read()
    regex: re.Pattern[str] = re.compile(r"pub\s+(async )?fn\s+([\w_]+(?:<\w+>)?)\s*(\(.*?\))\s*(?:->\s*([\w_:<>(\[\]), ;&']+))?\s*[{,where]", re.DOTALL|re.MULTILINE)
    functions = [Function(*fn.groups()) for fn in regex.finditer(str_data)]
    return Module(mod_name, functions)

def gen_traits(name: str, modules: list[Module], is_async: bool):
    trait = ["pub trait "+name+" {"]
    for m in modules:
        funcs = [f for f in m.functions if f.async_pref] if is_async else [f for f in m.functions if f.async_pref is None]
        for f in funcs:
            async_pref = f"{f.async_pref} " if f.async_pref else ""
            rettype = f" -> {f.return_type}" if f.return_type else ""
            trait.append(f"    {async_pref}fn {f.name}{f.parameters}{rettype};")
    trait.append("}")

    impl = ["impl "+name+" for NameMe {"]

    for m in modules:
        prefix = f"{m.name}::" if m.name else ""

        funcs = [f for f in m.functions if f.async_pref] if is_async else [f for f in m.functions if f.async_pref is None]

        for f in funcs:
            async_pref = f"{f.async_pref} " if f.async_pref else ""
            await_suff = ".await" if f.async_pref else ""
            rettype = f" -> {f.return_type}" if f.return_type else ""
            param_names = [p.split(":")[0] for p in f.parameters.replace("(", "").split(",") if ":" in p]
            call_params = f"({','.join(param_names)})"
            impl.append(f"    {async_pref}fn {f.name}{f.parameters}{rettype}")
            impl.append("    {")
            impl.append(f"        {prefix}{f.name.replace('<', '::<')}{call_params}{await_suff}")
            impl.append("    }")
    impl.append("}")

    print("\n".join(trait))
    print("\n".join(impl))

if __name__ == "__main__":
    dirname = sys.argv[1]
    traitname = sys.argv[2]

    modules = [parse_file(Path(filename)) for filename in glob.glob(f"{dirname}/src/**/*.rs", recursive=True)]
    gen_traits(f"Async{traitname}", modules, True)
    gen_traits(f"{traitname}", modules, False)
