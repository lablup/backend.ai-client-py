def ask_yn(prompt: str = 'Are you sure?', default: str = 'y') -> bool:
    if default == 'y':
        choices = 'Y/n'
    elif default == 'n':
        choices = 'y/N'
    else:
        raise ValueError("default must be given either 'y' or 'n'.")
    while True:
        user_reply = input("{0} [{1}] ".format(prompt, choices)).lower()
        if user_reply == '':
            user_reply = default
        if user_reply in ('y', 'yes', 'n', 'no'):
            break
        else:
            print("Please answer in y/yes/n/no.")
    if user_reply[:1].lower() == 'y':
        return True
    return False
