from typing import Callable


class Tool:
    def __init__ (self, name: str, function: Callable, description: str, params: dict[str, dict[str, any]], constraints: str, usage_examples: list[str]):
        self.name = name
        self.function = function
        self.description = description
        self.params = params
        self.constraints = constraints
        self.usage_examples = usage_examples

    def get_tool_information(self) -> str:
        info = [f"**{self.name}**", f"{self.description}", "", "Parameters:"]

        for param_name, param_info in self.params.items():
            required = "REQUIRED" if param_info.get("required", False) else "OPTIONAL"
            info.append(f"  - `{param_name}` ({param_info['type']}, {required}): {param_info['description']}")

        # Constraints
        if self.constraints:
            info.append("")
            info.append("Constraints:")
            info.append(f"  {self.constraints}")

        # Usage examples
        if self.usage_examples:
            info.append("")
            info.append("Use when:")
            for example in self.usage_examples:
                info.append(f"  - {example}")

        return "\n".join(info)