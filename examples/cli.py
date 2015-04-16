import sys
sys.path.append("..") # this isn't necessary outside of my testing
import destipy


def main(api_user):    
    cmd = input("Enter a command [lc=list characters, exit=exit the program]: ")
    if cmd == 'lc':
        for _, character in enumerate(api_user.characters):
            print("%s: %s" % (_, character))
    elif cmd == 'weekly':
        character_selection = input("Select a character: ")
        character = api_user.characters[int(character_selection)]
        print(character.weekly_heroic_status)
    elif cmd == 'exit':
        sys.exit()
    else:
        print("Command not found")
    # character = api_user.characters[0]
    # print(character)
    # pprint(character.character_info)
    # raids = hash_dict['raids']
    # for k, v in raids.iteritems():
       #  completed = character._raid_activity_status(k)
       #  print('%s %s' % (v, completed))

if __name__ == '__main__':
    valid_platforms = {'1': 'XBOX', '2': 'PS'}
    platform = input("Enter your platform [XBOX=1, PS=2]: ")
    platform_selection = valid_platforms.get(platform)
    if not platform_selection:
        print("Invalid platform: Enter 1 for XBOX or 2 for PS")
    else:
        print("Platform selected: %s" % platform_selection)
        username = input("Enter your username: ")
        api_user = destipy.DestinyUser(platform, username)
        if api_user.membership_id == 0:
            print("Invalid username")
        else:
            print("Successfully looked up: %s (%s)" % 
                (username, api_user.membership_id))
            while True:
                main(api_user)