def read_custom_key_value(line: str, cast=None):
    result = []
    for argument in line.split(","):
        splitted_arg = argument.split("=")
        if cast is not None:
            splitted_arg[1] = eval(cast)(splitted_arg[1])
        result.append((splitted_arg[0], splitted_arg[1]))
    return result


def read_args_list(args_list, cast=None, separator=","):
    splitted = args_list.split(separator)
    if cast is not None:
        for i in range(len(splitted)):
            splitted[i] = eval(cast)(splitted[i])
    return splitted