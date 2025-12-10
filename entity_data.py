import html
import os
import re
from dataclasses import dataclass
from os.path import expanduser
from typing import Dict, List, Optional


@dataclass
class EntityData:
    field_name: str
    data_type: str
    index: int


@dataclass
class EntityClass:
    name: str
    super_class: Optional[str]
    data_fields: List[EntityData]
    file_path: str


def format_class_name(class_name: str) -> str:
    # Add spaces between words
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', class_name)


def generate_entity_table(entity_class: EntityClass) -> str:
    cols = ['Index', 'Data Type', 'Field Name']
    col_widths = {col: len(col) for col in cols}

    # Calculate column widths
    for field in entity_class.data_fields:
        row = {
            'Index': str(field.index),
            'Data Type': html.escape(field.data_type),
            'Field Name': field.field_name
        }
        for key, value in row.items():
            col_widths[key] = max(col_widths[key], len(value))

    # Generate table
    header = "| " + " | ".join(f"{col:{col_widths[col]}}" for col in cols) + " |"
    separator = "|" + "|".join("-" * (width + 2) for width in col_widths.values()) + "|"

    rows = []
    for field in entity_class.data_fields:
        # Escape data type '<'
        data_type = html.escape(field.data_type)
        row = {
            'Index': str(field.index),
            'Data Type': data_type,
            'Field Name': field.field_name
        }
        rows.append("| " + " | ".join(f"{row[col]:{col_widths[col]}}" for col in cols) + " |")

    return "\n".join([header, separator] + rows)


def generate_overview_tree(sorted_classes: List[EntityClass]) -> str:
    # Create an ugly "tree"
    tree = {}
    for entity_class in sorted_classes:
        if entity_class.super_class:
            if entity_class.super_class not in tree:
                tree[entity_class.super_class] = []
            tree[entity_class.super_class].append(entity_class.name)
        else:
            if entity_class.name not in tree:
                tree[entity_class.name] = []

    # Function to recursively build the table
    def build_tree_table(class_name: str, indent: str) -> List[str]:
        rows = []
        if class_name in tree:
            rows.append(f"{indent}- [{class_name}](#{class_name.lower().replace(' ', '-')})")
            for subclass in tree[class_name]:
                rows.extend(build_tree_table(subclass, indent + "  "))
        return rows

    # Generate the table from the tree
    rows = []
    for class_name in tree:
        if not any(class_name in subclasses for subclasses in tree.values()):  # Only top-level classes
            rows.extend(build_tree_table(class_name, ""))

    return "\n".join(rows)


class MinecraftEntityAnalyzer:

    def __init__(self, source_dir: str):
        self.source_dir = source_dir
        self.entity_classes: Dict[str, EntityClass] = {}

        # To find fields like: EntityDataAccessor<Boolean> DATA_CUSTOM_NAME_VISIBLE = SynchedEntityData.defineId(Entity.class, EntityDataSerializers.BOOLEAN);
        self.data_pattern = re.compile(
            r'EntityDataAccessor<((?:[^<>]+|<(?:[^<>]+|<[^<>]+>)+>)*)>\s+([A-Z_\d]+)\s*=\s*'
            r'SynchedEntityData\.defineId\s*\(\s*([^,]+?)\s*\.class\s*,\s*EntityDataSerializers\.([^)]+?)\s*\)',
            re.DOTALL # Ignores line breaks
        )

        # Make sure we handle nested classes, like Display subtypes
        self.class_pattern = re.compile(
            r'class\s+(\w+)(?:\s+extends\s+([\w.]+))?(?:\s+implements\s+[^{]+)?\s*{'
        )

    def parse_java_file(self, file_path: str) -> Optional[List[EntityClass]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract class names and superclasses, including nested classes
        class_matches = self.class_pattern.findall(content)
        if not class_matches:
            return None

        entity_classes = []
        for match in class_matches:
            class_name = match[0]
            super_class = match[1] if match[1] else None

            # Find all entity data definitions for the class
            data_fields = []
            for data_match in self.data_pattern.finditer(content):
                data_type, field_name, entity_class, serializer = data_match.groups()

                # Check for nested classes
                if entity_class == class_name or entity_class.endswith(f".{class_name}"):
                    # Clean up names slightly, though they will still be incredibly inconsistent
                    field_name = field_name.replace('DATA_ID_', '').replace('DATA_', '').replace('_ID', '')
                    data_type = data_type.strip()
                    serializer = serializer.strip()

                    data_fields.append(EntityData(
                        field_name=field_name,
                        data_type=data_type,
                        index=-1
                    ))

            # Also prettify class names
            class_name = format_class_name(class_name)
            if super_class is not None:
                super_class = format_class_name(super_class)

            entity_classes.append(EntityClass(
                name=class_name,
                super_class=super_class,
                data_fields=data_fields,
                file_path=file_path
            ))

        return entity_classes

    def find_entity_files(self):
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    entity_classes = self.parse_java_file(file_path)
                    if entity_classes:
                        for entity_class in entity_classes:
                            self.entity_classes[entity_class.name] = entity_class

    def get_inheritance_chain(self, class_name: str) -> List[str]:
        chain = []
        current = class_name
        while current and current in self.entity_classes:
            chain.append(current)
            current = self.entity_classes[current].super_class
        return list(reversed(chain))

    def calculate_indices(self):
        for class_name, entity_class in self.entity_classes.items():
            inheritance_chain = self.get_inheritance_chain(class_name)
            current_index = 0

            for parent_class in inheritance_chain[:-1]:
                current_index += len(self.entity_classes[parent_class].data_fields)

            for field in entity_class.data_fields:
                field.index = current_index
                current_index += 1

    def generate_report(self) -> str:
        # Include all Entity subclasses, even if they have no data
        sorted_classes = sorted(
            [ec for ec in self.entity_classes.values()
             if ec.data_fields or 'Entity' in self.get_inheritance_chain(ec.name)],
            key=lambda c: (len(self.get_inheritance_chain(c.name)), c.name)
        )

        sections = ["# Minecraft Entity Data Fields\n"]

        # Overview table
        sections.append("## Overview\n")
        sections.append(generate_overview_tree(sorted_classes))
        sections.append("\n")

        # Individual entity sections
        sections.append("## Entity Details\n")
        for entity_class in sorted_classes:
            # Entity header
            super_link = (f"[{entity_class.super_class}](#{entity_class.super_class.lower().replace(' ', '-')})"
                          if entity_class.super_class in self.entity_classes
                          else (entity_class.super_class or "None"))

            sections.append(f"### {entity_class.name}")
            sections.append(f"**Extends:** {super_link}\n")

            # Entity's data entires
            if entity_class.data_fields:
                sections.append(generate_entity_table(entity_class))
            else:
                sections.append("No data.")
            sections.append("\n")

        return "\n".join(sections)


def main(file_name: str, last_content: str) -> str:
    # source_dir = os.path.join("src", "main", "java", "net", "minecraft", "world", "entity")
    source_dir = expanduser(os.path.join("~", "IdeaProjects", "MCSources", "src", "main", "java", "net", "minecraft", "world", "entity"))

    analyzer = MinecraftEntityAnalyzer(source_dir)
    analyzer.find_entity_files()
    analyzer.calculate_indices()

    report = analyzer.generate_report()

    # Save to file
    if report != last_content:
        with open(f'docs/{file_name}.md', 'w') as f:
            f.write(report)
    else:
        print('Same content as last.')
    return report


if __name__ == "__main__":
    main('entity_data', 'entity-data')
