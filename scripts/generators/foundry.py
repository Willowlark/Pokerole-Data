from glob import glob
import json
import os
from shutil import copy
from os.path import join
import fire
import datetime

secrets = json.load(open('../../secrets.json'))

# Moves with fields that are problematic for the export
# - Any Move is too generic, individual moves can be added to Mew instead
# - Struggle, Growl and Photon Geyser have attributes like "Strength/special", but there are specialized versions for each attribute
IGNORED_MOVES = ['any-move', 'struggle', 'growl', 'photon-geyser']

# Stabilize An Ally is usually only used by trainers (Pokémon don't have the Medicine skill)
DEFAULT_POKEMON_MANEUVERS = ['Struggle (Physical)', 'Struggle (Special)', 'Grapple', 'Help Another', 'Cover an Ally', 'Run Away']

class Foundry(object):
    
    def __init__(self, system_version, version="Version20"):
        self.path_setup(version)
        self.system_version = system_version
        self.version = version
        self.display_version = "Core 2.0"

    def path_setup(self, version):
        
        self.pokedex_path = f'../../{version}/Pokedex'
        self.abilities_path = f'../../{version}/Abilities'
        self.moves_path = f'../../{version}/Moves'
        self.learnsets_path = f'../../{version}/Learnsets'
        self.natures_path = f'../../{version}/Natures'
        self.sprites_path = '../../Images/BoxSprites/'
        self.home_path = '../../Images/HomeSprites/'
        self.book_path = '../../Images/BookSprites/'
        self.shuffle_path = '../../Images/ShuffleTokens/'
        self.items_path = f'../../{version}/Items/'

        paths = [self.pokedex_path,self.abilities_path,self.moves_path,
        self.learnsets_path,self.natures_path,self.sprites_path,
        self.home_path,self.book_path,self.shuffle_path,self.items_path]
        
        for p in paths:
            if not os.path.exists(p): raise Exception(f"ERROR: Path {p} not found!")
            
        self.pokedex_output = f"{secrets['FoundryDataDir']}/packs/"
        self.abilities_output = f"{secrets['FoundryDataDir']}/packs/"
        self.moves_output = f"{secrets['FoundryDataDir']}/packs/"
        self.learnsets_output = f"{secrets['FoundryDataDir']}/packs/"
        self.natures_output = f"{secrets['FoundryDataDir']}/packs/"
        self.sprites_output = f"{secrets['FoundryDataDir']}/images/pokemon/box/"
        self.home_output = f"{secrets['FoundryDataDir']}/images/pokemon/home/"
        self.book_output = f"{secrets['FoundryDataDir']}/images/pokemon/book/"
        self.shuffle_output = f"{secrets['FoundryDataDir']}/images/pokemon/shuffle/"
        self.items_output = f"{secrets['FoundryDataDir']}/packs/"

        self.outputs = [self.pokedex_output,self.abilities_output,self.moves_output,
                    self.learnsets_output,self.natures_output,self.sprites_output,
                    self.home_output,self.book_output,self.shuffle_output,self.items_output]

        for p in self.outputs:
            os.makedirs(p,exist_ok=True)
            
        return 0

    def _pokedex(self, sheet_img='book', token_img='book'):
        sheet_img = sheet_img.lower() if sheet_img.lower() in ['book', 'box', 'home', 'shuffle'] else 'book'
        token_img = token_img.lower() if token_img.lower() in ['book', 'box', 'home', 'shuffle'] else 'book'
        db = []
        try:
            for src in glob(self.pokedex_path+"/*.json"):
                entry = json.loads(open(src).read())
                id = entry['_id'].replace(".", "") # "mime-jr." workaround
                
                learnset = json.loads(open(join(self.learnsets_path, f"{entry['Name']}.json")).read())
                moves = []
                ranks = []
                for x in learnset['Moves']:
                    if x['Name'] == "Growl": # Use the two versions of Growl since it would otherwise be skipped over
                        moves.append('Growl (Tough)')
                        ranks.append(x['Learned'])
                        moves.append('Growl (Cute)')
                        ranks.append(x['Learned'])
                    elif x['Name'] == "Photon Geyser":
                        moves.append('Photon Geyser (Physical)')
                        ranks.append(x['Learned'])
                        moves.append('Photon Geyser (Special)')
                        ranks.append(x['Learned'])
                    else:
                        moves.append(x['Name'])
                        ranks.append(x['Learned'])

                moves += DEFAULT_POKEMON_MANEUVERS
                ranks += ['starter'] * len(DEFAULT_POKEMON_MANEUVERS)
                move_list = self._moves(moves, ranks)

                abilities = self._abilities([entry['Ability1'], entry['Ability2']])
                hidden_ability_list = self._abilities([entry['HiddenAbility']])
                if len(hidden_ability_list) > 0:
                    ability = hidden_ability_list[0]
                    ability["name"] += " [Hidden Ability]"
                    abilities.append(ability)
                event_ability_list = self._abilities([entry['EventAbilities']])
                if len(event_ability_list) > 0:
                    ability = event_ability_list[0]
                    ability["name"] += " [Event]"
                    abilities.append(ability)

                foundry_items = move_list+abilities
                
                for move in move_list:
                    move["ownership"] = { "default": 0, f"pokemon-{id}": 3}
                
                foundry = {
                            "_id": f"pokemon-{id}",
                            "name": entry['Name'],
                            "type": "pokemon",
                            "img": f"systems/pokerole/images/pokemon/{sheet_img}/{entry['Image']}",
                            "system": {
                                "hp": {
                                    "value": entry['Vitality']+entry['BaseHP'],
                                    "min": 0,
                                    "max": entry['Vitality']+entry['BaseHP']
                                },
                                "will": {
                                    "value": 2+entry['Insight'],
                                    "min": 0,
                                    "max": 2+entry['Insight']
                                },
                                "baseHp": entry['BaseHP'],
                                "rank": "none",
                                "recommendedRank": entry['RecommendedRank'].lower(),
                                # Nature is named "personality" internally to avoid conflicts with the "Nature" skill
                                "personality": "hardy",
                                "confidence": 0,
                                "attributes": {
                                "strength": {
                                    "value": entry['Strength'],
                                    "min": 0,
                                    "max": entry['MaxStrength']
                                },
                                "dexterity": {
                                    "value": entry['Dexterity'],
                                    "min": 0,
                                    "max": entry['MaxDexterity']
                                },
                                "vitality": {
                                    "value": entry['Vitality'],
                                    "min": 0,
                                    "max": entry['MaxVitality']
                                },
                                "special": {
                                    "value": entry['Special'],
                                    "min": 0,
                                    "max": entry['MaxSpecial']
                                },
                                "insight": {
                                    "value": entry['Insight'],
                                    "min": 0,
                                    "max": entry['MaxInsight']
                                },
                                },
                                "social": {
                                "tough": {
                                    "value": 1,
                                    "min": 0,
                                    "max": 5
                                },
                                "cool": {
                                    "value": 1,
                                    "min": 0,
                                    "max": 5
                                },
                                "beauty": {
                                    "value": 1,
                                    "min": 0,
                                    "max": 5
                                },
                                "cute": {
                                    "value": 1,
                                    "min": 0,
                                    "max": 5
                                },
                                "clever": {
                                    "value": 1,
                                    "min": 0,
                                    "max": 5
                                }
                                },
                                "skills": {
                                "brawl": {
                                    "value": 0,
                                    "min": 0
                                },
                                "evasion": {
                                    "value": 0,
                                    "min": 0
                                },
                                "alert": {
                                    "value": 0,
                                    "min": 0
                                },
                                "athletic": {
                                    "value": 0,
                                    "min": 0
                                },
                                "nature": {
                                    "value": 0,
                                    "min": 0
                                },
                                "stealth": {
                                    "value": 0,
                                    "min": 0
                                },
                                "allure": {
                                    "value": 0,
                                    "min": 0
                                },
                                "etiquette": {
                                    "value": 0,
                                    "min": 0
                                },
                                "intimidate": {
                                    "value": 0,
                                    "min": 0
                                },
                                "perform": {
                                    "value": 0,
                                    "min": 0
                                },
                                "channel": {
                                    "value": 0,
                                    "min": 0
                                },
                                "clash": {
                                    "value": 0,
                                    "min": 0
                                }
                                },
                                "biography": "",
                                "battles": 0,
                                "victories": 0,
                                "pokedexId": entry['Number'],
                                "species": entry['Name'],
                                "pokedexCategory": entry['DexCategory'],
                                "pokedexDescription": entry['DexDescription'],
                                "type1": entry['Type1'].lower(),
                                "type2": entry['Type2'].lower(),
                                "height": entry['Height']['Meters'],
                                "weight": entry['Weight']['Kilograms'],
                                "extra": {
                                "happiness": {
                                    "value": 2,
                                    "min": 0,
                                    "max": 5
                                },
                                "loyalty": {
                                    "value": 2,
                                    "min": 0,
                                    "max": 5
                                }
                                },
                                "source": self.display_version,
                            },
                            "prototypeToken": {
                                "name": entry['Name'],
                                "displayName": 0,
                                "actorLink": False,
                                "texture": {
                                "src": f"systems/pokerole/images/pokemon/{token_img}/{entry['Image']}",
                                "scaleX": 1,
                                "scaleY": 1,
                                "offsetX": 0,
                                "offsetY": 0,
                                "rotation": 0,
                                "tint": None
                                },
                                "width": 1,
                                "height": 1,
                                "lockRotation": False,
                                "rotation": 0,
                                "alpha": 1,
                                "disposition": -1,
                                "displayBars": 0,
                                "bar1": {
                                "attribute": "hp"
                                },
                                "bar2": {
                                "attribute": "will"
                                },
                                "light": {
                                "alpha": 0.5,
                                "angle": 360,
                                "bright": 0,
                                "color": None,
                                "coloration": 1,
                                "dim": 0,
                                "attenuation": 0.5,
                                "luminosity": 0.5,
                                "saturation": 0,
                                "contrast": 0,
                                "shadows": 0,
                                "animation": {
                                    "type": None,
                                    "speed": 5,
                                    "intensity": 5,
                                    "reverse": False
                                },
                                "darkness": {
                                    "min": 0,
                                    "max": 1
                                }
                                },
                                "sight": {
                                "enabled": False,
                                "range": None,
                                "angle": 360,
                                "visionMode": "basic",
                                "color": None,
                                "attenuation": 0.1,
                                "brightness": 0,
                                "saturation": 0,
                                "contrast": 0
                                },
                                "detectionModes": [],
                                "flags": {},
                                "randomImg": False,
                            },
                            "items": foundry_items,
                            "effects": [],
                            "flags": {},
                            "_stats": {
                                "systemId": "pokerole",
                                "systemVersion": self.system_version,
                                "coreVersion": "10.291",
                                "createdTime": 1670952558737,
                                "modifiedTime": datetime.datetime.now().timestamp(),
                                "lastModifiedBy": "Generator"
                            }
                            }
                db.append(foundry)
        except:
            print(entry, moves, ranks)
            raise
        with open(self.pokedex_output+"pokedex.db",'w') as f:
            for x in db:
                f.write(json.dumps(x)+'\n')
    
    def _abilities(self, alist=None):
        
        db = []
        iter_target = glob(self.abilities_path+"/*.json") if not alist else [f"{self.abilities_path}/{x}.json" for x in alist if x]
        for src in iter_target:
            try:
                entry = json.loads(open(src).read())
            except FileNotFoundError as e:
                if alist: 
                    print(f"ERROR: Ability {src} not found.")
                    continue
                else: raise e

            foundry = {
                "_id": f"ability-{entry['_id']}",
                "name": entry['Name'],
                "type": "ability",
                "img": "icons/svg/book.svg",
                "system": {
                    "description": f"<p>{entry['Effect']}</p><p>{entry['Description']}</p>"
                },
                "effects": [],
                "source": self.display_version,
                "flags": {},
                "_stats": {
                    "systemId": "pokerole",
                    "systemVersion": self.system_version,
                    "coreVersion": "10.291",
                    "createdTime": 1670695293664,
                    "modifiedTime": datetime.datetime.now().timestamp(),
                    "lastModifiedBy": "Generator"
                }
            }

            db.append(foundry)
        if not alist:
            with open(self.abilities_output+"abilities.db",'w') as f:
                for x in db:
                    f.write(json.dumps(x)+'\n')
        return db
    
    def _moves(self, mlist=False, ranks=False):
        
        def _attribute_get(attr, value, default=False):
            if not attr: return default
            else: return attr.get(value) if attr.get(value) else default

        def _icon_for_type(type):
            if type == 'none':
                # TODO: is there anything better than Normal for typeless moves?
                return 'systems/pokerole/images/types/normal.svg'
            
            return f'systems/pokerole/images/types/{type}.svg'

        def _check_target(target):
            assert target in ["Foe", "Random Foe", "All Foes", "User", "One Ally", "User and Allies",
                "Area", "Battlefield", "Battlefield (Foes)", "Battlefield and Area"], f"Invalid target '{target}'"

        def _check_attribute(attr):
            assert attr in ["strength", "dexterity", "vitality", "special", "insight", "tough", "cool", "beauty", "cute", "clever", "will"], f"Invalid attribute '{attr}'"

        def _check_skill(attr):
            assert attr in ["brawl", "channel", "clash", "evasion", "alert", "athletic", "nature", "stealth", "allure", "etiquette", "intimidate", "perform", "crafts", "lore", "medicine", "science"], f"Invalid attribute '{attr}'"

        def _convert_heal_data(data):
            converted = { 'type': 'none' }
            if not data: return converted
            
            ty = data.get('Type')
            target = data.get('Target')
            will_point_cost = data.get('WillPointCost')
            percentage = data.get('Percentage')
            if not ty or not target:
                raise 'Type or target missing in heal data'

            if ty:
                converted['type'] = ty.lower()
            if target:
                converted['target'] = target.lower()
            converted['willPointCost'] = will_point_cost if will_point_cost else 0
            if percentage:
                converted['amount'] = percentage
            return converted
        
        db = []
        iter_target = glob(self.moves_path+"/*.json") if not mlist else [f"{self.moves_path}/{x}.json" for x in mlist]
        for src in iter_target:
            try:
                entry = json.loads(open(src).read())
            except FileNotFoundError as e:
                if mlist: 
                    print(f"ERROR: move {src} not found.")
                    continue
                else: raise e
            attr = entry.get("Attributes")
            id = entry['_id']

            if id in IGNORED_MOVES:
                continue

            accMod1 = entry['Accuracy1'].lower()
            accMod2 = entry['Accuracy2'].lower()
            dmgMod = entry['Damage1'].lower()
            move_type = entry['Type'].lower()
            description = entry['Description']
            effect = entry['Effect']

            # Remove empty added effects
            if effect == '-':
                effect = ''

            if move_type == "typeless":
                move_type = "none"

            # Special cases that can't be rolled automatically
            if id == 'lovely-kiss':
                accMod1 = ''
                accMod2 = ''
                effect += ' Roll (5 - Beauty) + Allure dice for accuracy.'
            if id == 'simple-beam':
                accMod1 = ''
                accMod2 = ''
                effect += ' Roll Insight+Empathy dice for accuracy. See the description for more details.'
                description += "<p>Empathy is a custom skill, which you can add manually on the Pokémon's character sheet. You can edit this move to auto-roll once you've added the skill by setting Accuracy Modifier 1 to 'insight' and Accuracy Modifier 2 to 'empathy'.</p>";
            if id == 'copycat':
                accMod1 = ''
                accMod2 = ''
                dmgMod = ''
                effect += ' Use the same dice pool for accuracy and damage.'
            if id == 'help-another':
                accMod1 = ''
                accMod2 = ''

            # Data consistency checks
            _check_target(entry['Target'])
            if accMod1 != '':
                _check_attribute(accMod1)
            if accMod2 != '':
                _check_skill(accMod2)
            if dmgMod != '':
                _check_attribute(dmgMod)

            foundry = {
                        "_id": f"move-{id}",
                        "name": entry['Name'],
                        "type": "move",
                        "img": _icon_for_type(move_type),
                        "system": {
                            "description": description,
                            "type": move_type,
                            "category": entry['DmgType'].lower(),
                            # Special case for Spider Web
                            "target": entry['Target'] if id != 'spider-web' else "Battlefield (Foes)",
                            "power": entry['Power'],
                            "accMod1": accMod1,
                            "accMod2": accMod2,
                            "dmgMod": dmgMod,
                            "effect": effect,
                            "source": self.display_version,
                            "attributes": {
                                "accuracyReduction":   _attribute_get(attr, "AccuracyReduction", 0),
                                "priority":            _attribute_get(attr, "Priority", 0),
                                "highCritical":        _attribute_get(attr, "HighCritical"),
                                "lethal":              _attribute_get(attr, "Lethal"),
                                "physicalRanged":      _attribute_get(attr, "PhysicalRanged"),
                                "charge":              _attribute_get(attr, "Charge"),
                                "mustRecharge":        _attribute_get(attr, "MustRecharge"),
                                "fistBased":           _attribute_get(attr, "FistBased"),
                                "soundBased":          _attribute_get(attr, "SoundBased"),
                                "shieldMove":          _attribute_get(attr, "ShieldMove"),
                                "neverFail":           _attribute_get(attr, "NeverFail"),
                                "switcherMove":        _attribute_get(attr, "SwitcherMove"),
                                "recoil":              _attribute_get(attr, "Recoil"),
                                "rampage":             _attribute_get(attr, "Rampage"),
                                "doubleAction":        _attribute_get(attr, "DoubleAction"),
                                "alwaysCrit":          _attribute_get(attr, "AlwaysCrit"),
                                "destroyShield":       _attribute_get(attr, "DestroyShield"),
                                "successiveActions":   _attribute_get(attr, "SuccessiveActions"),
                                "userFaints":          _attribute_get(attr, "UserFaints"),
                                "resetTerrain":        _attribute_get(attr, "ResetTerrain"),
                                "resistedWithDefense": _attribute_get(attr, "ResistedWithDefense"),
                                "ignoreDefenses":      _attribute_get(attr, "IgnoreDefenses"),
                                "maneuver":            move_type == "none"
                            },
                            "heal": _convert_heal_data(entry['AddedEffects'].get('Heal')),
                        },
                        "effects": [],
                        "flags": {},
                        "folder": None,
                        "sort": 100001,
                        "_stats": {
                            "systemId": "pokerole",
                            "systemVersion": self.system_version,
                            "coreVersion": "10.291",
                            "createdTime": 1670525752873,
                            "modifiedTime": datetime.datetime.now().timestamp(),
                            "lastModifiedBy": "Generator"
                        }
            }
            if ranks and len(ranks) == len(iter_target):
                foundry['system']['rank'] = ranks[iter_target.index(src)].lower()
            db.append(foundry)
        if not mlist:
            with open(self.moves_output+"moves.db",'w') as f:
                for x in db:
                    f.write(json.dumps(x)+'\n')
        return db
    
    def _learnsets(self):
        pass
    
    def _natures(self):
        pass
    
    def _items(self):
        pass
            
    def _images(self):
        def x(path, output):
            for img in [x for x in os.listdir(path) if '.png' in x]:
                copy(path+img, output+img)
        x(self.sprites_path, self.sprites_output)
        x(self.home_path, self.home_output)
        x(self.book_path, self.book_output)
        x(self.shuffle_path, self.shuffle_output)
        
def update( *argv,
            system_version,
            batch=False, 
            version='Version20', 
            confirm=False,
            sheet_images='book',
            token_images='book'):
        
    foundry = Foundry(system_version, version)
    
    targets = {
        "pokedex":   foundry._pokedex,
        "abilities": foundry._abilities,
        "moves":     foundry._moves,
        "learnsets": foundry._learnsets,
        "natures":   foundry._natures,
        "items":     foundry._items,
        "images":    foundry._images
    }
    
    updates = list(targets.keys()) if batch else []
    for t in argv:
        if t.lower() in targets:
            updates.append(t.lower())
        else:
            print(f"WARN: Target {t.lower()} not configured, Skipping...")
    updates = set(updates)
    if not confirm: 
        conf = input(f'INFO: {updates}\nQUERY: Update these folders in Foundry? [Y/Yes]: ')
        if conf.lower() not in ['y', 'yes']:
            return "WARN: Did not confirm update, cancelling..."
    else: print(f'INFO: {updates}\nQUERY: Updating these folders in the Foundry...')
    
    for t in updates:
        func = targets[t]
        if t == 'pokedex': func(sheet_images, token_images)
        else: func()
        print(f'INFO: Folder {t} updated!')
        
    print('INFO: Foundry Update Complete.')
        
def help():
    print("""
    Python Script to update the Obsidian Foundry with the latest Data. 
    
    update: 
        update --system_version Version [collection names], [--batch] [--version Version] [--confirm] [--sheet_images src] [--token_images src]
            system_version       : The target Foundry system version.
            collection names     : one or more of the folders in Foundry. Optional when using --batch.
            batch                : Optional. Updates all Foundry folderss
            version              : Optional. Changes the Version folder to be used in paths.
            confirm              : Optional. Skips confirmation step. 
            sheet_images         : Optional. Source of pokemon sheet images. Either 'book', 'home', 'box', or 'shuffle'.
            token_images         : Optional. Source of pokemon token images. Either 'book', 'home', 'box', or 'shuffle'.
    """)

if __name__ == '__main__':
    fire.Fire()
    
