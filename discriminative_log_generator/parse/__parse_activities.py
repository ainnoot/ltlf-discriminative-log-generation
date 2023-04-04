__all__ = ['parse_activity_block']


class InvalidActivityException(Exception):
    def __int__(self, activity):
        super().__init__(f"\"{activity}\" does not match [a-z][a-z_0-9]*.")


class MissingMaskException(Exception):
    def __init__(self, block):
        super().__init__(f"Mask has not been specified! {block}")


class MaskWrongTypeException(Exception):
    def __init__(self, block):
        super().__init__(f"Mask should be a string, but found {block}")


class MaskKeywordException(Exception):
    def __init__(self, mask, expected, keywords):
        super().__init__(f"The mask {mask} requires EXACTLY these keywords: {expected}, but {keywords} are provided.")


class UnknownBlock(Exception):
    def __init__(self, block):
        super().__init__(f"Unknown block: {block}")


class WrongType(Exception):
    def __init__(self, name, type_, expected):
        super().__init__(f"Attribute {name} needs to be of type {expected}, but found {type_}")


class RangeMissingParameters(Exception):
    def __init__(self, block):
        super().__init__(f"Using ranges requires exactly `start` and `end` values. {block}")


class RangeInvalidParametersTypes(Exception):
    def __init__(self, start, end):
        super().__init__(f"Start and End must be integers, found {start=}, {end=}")


class InvalidRange(Exception):
    def __init__(self, start, end):
        super().__init__(f"Start must be less than end, found {start=}, {end=}")


def extract_keywords(string):
    """
    Returns the set of replaceable keywords in a string.

    :param string: An f-string.
    :return: A :class:`set` of keywords.
    """
    from string import Formatter
    parameters = []

    for _, fname, _, _ in Formatter().parse(string):
        if len(fname) == 0:
            raise Exception("No unnamed parameters.")
        parameters.append(fname)

    return set(parameters)


def validate_activity(activity):
    from re import fullmatch
    if not fullmatch(r"[a-z][a-z_0-9]*", activity):
        raise InvalidActivityException(activity)


def validate_activity_list(activity_list):
    for activity in activity_list:
        validate_activity(activity)


def validate_activity_shorthand(activity_shorthand):
    if 'mask' not in activity_shorthand:
        raise MissingMaskException(activity_shorthand)

    if type(activity_shorthand['mask']) is not str:
        raise MaskWrongTypeException(activity_shorthand)

    keywords = extract_keywords(activity_shorthand['mask'])
    keys = set(activity_shorthand.keys())
    keys.remove('mask')

    if keywords != keys:
        raise MaskKeywordException(activity_shorthand['mask'], keywords, keys)

    for keyword in keywords:
        if isinstance(activity_shorthand[keyword], list):
            for value in activity_shorthand[keyword]:
                if type(value) != int and type(value) != str:
                    raise WrongType(value, type(value), [int, str])

        elif isinstance(activity_shorthand[keyword], dict):
            if set(activity_shorthand[keyword].keys()) != {'start', 'end'}:
                raise RangeMissingParameters(activity_shorthand[keyword])

            if type(activity_shorthand[keyword]['start']) != int:
                raise RangeInvalidParametersTypes(activity_shorthand[keyword]['start'], activity_shorthand[keyword]['end'])

            if type(activity_shorthand[keyword]['end']) != int:
                raise RangeInvalidParametersTypes(activity_shorthand[keyword]['start'], activity_shorthand[keyword]['end'])

            if activity_shorthand[keyword]['start'] >= activity_shorthand[keyword]['end']:
                raise InvalidRange(activity_shorthand[keyword]['start'], activity_shorthand[keyword]['end'])

        else:
            raise UnknownBlock(keyword)


def parse_activity_block(block):
    activities = []
    for content in block:
        if isinstance(content, str):
            validate_activity(content)
            activities.append(content)

        elif isinstance(content, list):
            validate_activity_list(content)
            activities.extend(content)

        elif isinstance(content, dict):
            validate_activity_shorthand(content)
            mask = content['mask']

            domains = dict()
            for key, values in content.items():
                if type(values) == list:
                    domains[key] = values

                elif type(values) == dict:
                    domains[key] = list(range(values['start'], values['end']+1))

            sorted_keys = sorted(domains.keys())
            sorted_domains = [domains[k] for k in sorted_keys]
            del domains

            from itertools import product
            for replacement in product(*sorted_domains):
                activities.append(mask.format(**{k: v for k, v in zip(sorted_keys, replacement)}))

        else:
            raise UnknownBlock(content)

    return set(activities)


if __name__ == '__main__':
    example = """
    activities:
        - a
        - b
        - [x, y]
        - [q, t]
        - mask: a_{i}_{q}
          i: [1, 2]
          q: 
            start: 4
            end: 5
    """

    import yaml
    data = yaml.safe_load(example)
    print(parse_activity_block(data['activities']))