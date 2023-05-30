import os
import pickle
from defines import UTF8_BOM

settings_file = "./settings.pkl"
# load settings if it exists, otherwise create an empty dictionary for it
if not os.path.exists(settings_file):
    settings = {}
else:
    with open(settings_file, 'rb') as f:
        settings = pickle.load(f)

gamedir = "gamedir"
if gamedir not in settings:
    gamedir_response = input(
        "Enter the path to your game directory: e.g. C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game")
    settings[gamedir] = gamedir_response

# save settings
with open(settings_file, 'wb') as f:
    pickle.dump(settings, f)


def create_combined_compatible_file(relative_path, enclosing_scope_name, game_directory=None):
    """
    Create a merged copy of a file that is compatible with the game.
    Look for our source under relative_path, find the same game file under the game_directory and merge them by
    adding our file content at the end, preceding a specified number of closing braces.

    :param relative_path: relative path to the file we want to merge
    :param enclosing_scope_name: name or fullname of the enclosing scope you want to add the file's content to. e.g.
    "western_royalty" will search for the block western_royalty = { ... and add the file's content before the closing
    brace. A fullname or partial scoped named like "cloaks:western_royalty" can also be used, which will search for
    the block cloaks = { ... western_royalty = { ... and add the file's content before the closing brace of the
    inside western_royalty block.
    :param game_directory: None to specify the game directory, otherwise a full path to for example another mod like CPF
    e.g. C:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\2220098919
    :return:
    """
    # look for our file under `src`
    src_file = os.path.join("src", relative_path)
    with open(src_file, 'r', encoding='utf-8') as f:
        src_content = f.read().strip(UTF8_BOM)
    output_path = relative_path
    if game_directory is not None:
        # strip off last directory of game_directory
        output_path = os.path.join(os.path.basename(os.path.normpath(game_directory)), relative_path)
        output_path = os.path.normpath(output_path)
    # look for the game file under the game directory
    if game_directory is None:
        game_directory = settings[gamedir]
    game_file = os.path.join(game_directory, relative_path)
    game_file = os.path.normpath(game_file).strip()
    # if the game file doesn't exist, skip it
    if not os.path.exists(game_file):
        print("Skipping " + game_file + " because it doesn't exist.")
        return

    with open(game_file, 'r', encoding='utf-8') as f:
        game_content = f.read().strip(UTF8_BOM)

    # find the innermost enclosing scope
    scopes = enclosing_scope_name.split(":")
    idx = 0
    for scope in scopes:
        idx = game_content.find(scope, idx)
        if idx == -1:
            raise Exception("Couldn't find scope " + scope + " in " + game_file)
    # we are now at the start of the scope name, go to the end of the scope by finding the matching brace
    istart = []
    i = 0
    for i, c in enumerate(game_content[idx:]):
        if c == '{':
            istart.append(i)
        elif c == '}':
            istart.pop()
            if not istart:
                break
    idx += i

    # insert src_content before the last num_trailing_braces closing braces
    # go back to the first non-whitespace character
    while game_content[idx - 1] in [" ", "\t", "\n", "\r"]:
        idx -= 1
    # insert src_content before the last num_trailing_braces closing braces
    game_content = game_content[:idx] + '\n' + src_content + game_content[idx:]
    # write the combined content to a copy of the game file at relative_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print("Writing combined file to " + output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(UTF8_BOM)
        f.write(game_content)
    return game_content


game_dir = input(
    "Enter the path to the game directory to make compatible files for, or leave blank to use the game directory.\n"
    "This can be used to specify a mod, e.g. C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/2220098919\n")
if game_dir.strip() == "":
    game_dir = None

# put any other files that need to be made compatible here
create_combined_compatible_file("gfx/portraits/portrait_modifiers/00_custom_clothes.txt", "custom_clothes", game_dir)
create_combined_compatible_file("gfx/portraits/portrait_modifiers/00_custom_headgear.txt", "custom_headgear", game_dir)
create_combined_compatible_file("common/genes/05_genes_special_accessories_clothes.txt", "accessory_genes:clothes", game_dir)
create_combined_compatible_file("common/genes/06_genes_special_accessories_headgear.txt", "accessory_genes:headgear", game_dir)
create_combined_compatible_file("gfx/portraits/portrait_modifiers/CFP_necklaces.txt", "cfp_necklaces", game_dir)
create_combined_compatible_file("common/genes/CFP_genes_special_accessories_necklaces.txt", "special_accessories_necklace", game_dir)
create_combined_compatible_file("gfx/portraits/portrait_modifiers/CFP_custom_necklaces.txt", "custom_necklace", game_dir)
