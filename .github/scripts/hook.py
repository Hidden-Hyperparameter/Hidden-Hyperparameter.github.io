import os,re
father = './_posts'

def get_tags(content):
    # match the following:
    # tags:
    # - tag1
    # - tag2
    lines = content.split('\n')
    i = 0
    for i in range(len(lines)):
        if 'tags:' in lines[i]:
            break
    i += 1
    tags = []
    while i < len(lines):
        if not lines[i].strip().startswith('-'):
            break
        val = lines[i].strip().strip('-').strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        tags.append(val)
        i += 1
    return [c.strip() for c in tags]

def check_format(title,content):
    errors = []
    content = content.replace(r'\left|','')
    content = content.replace(r'\right|','')
    content = content.replace(r'\|','')

    lines = content.split('\n')
    for i,line in enumerate(lines):
        if '|' in line and not (line.strip().startswith('|') and not line.strip().endswith('|')):
            errors.append(f'💩💩Fatal💩💩: File {title}, line {i+1} contains invalid `|`. You should use `|` properly, see README.md for more information')
    return errors

# All error messages
ALL_ERROR_MSGS = []

# check tags
all_tags = set()

for md_file in os.listdir(father):
    if not md_file.endswith('.md'):
        continue
    with open(os.path.join(father,md_file), 'r') as f:
        content = f.read()
        new_tags = get_tags(content)
        for c in new_tags:
            if (not c in all_tags) and c.lower() in {v.lower() for v in all_tags}:
                expected_tag = [v for v in all_tags if v.lower() == c.lower()][0]
                ALL_ERROR_MSGS.append(f'💩💩Fatal💩💩: Tag Duplicate: {md_file} has duplicated tags: {c}, should be {expected_tag}')
        all_tags.update(new_tags)
        ALL_ERROR_MSGS.extend(check_format(md_file,content))

if len(ALL_ERROR_MSGS) > 0:
    print(f'Your commit has {len(ALL_ERROR_MSGS)} error(s) 💣💣💣:\n===')
    print('\n===\n'.join(ALL_ERROR_MSGS))
    exit(1)