from typing import List, Dict, Union

# Begin helper functions
def ensure_address_format(prefix, address):
    if not address.startswith(prefix):
        address = "{}{}".format(prefix, address)
    return address

def get_element_list(target: List[str], delimiter: str, index: int,
                     strip_whitespace=True) -> List[str]:
    element_list = []
    for line in target:
        # Split
        tokenized_list = line.split(delimiter)
        # Select
        element = tokenized_list[index]
        if strip_whitespace:
            # Strip
            element = element.strip()
        element_list.append(element)
    return element_list

def parse_payment_addresses(addresses: List[str], delimiter: str,
                            index: int) -> List[str]:
    return get_element_list(addresses, delimiter, index)

def parse_payment_sources(sources: List[str]) -> Dict[str,Dict[str,Union[int,str]]]:
    payment_sources = {}
    for source in sources:
        source_attributes = source.split("|")
        # Convert amount to an int here for convenience later
        amount = source_attributes[3].strip()
        if amount == '':
            amount = "0"
        extra = source_attributes[4].strip()
        if extra == '':
            extra = "0"
        payment_sources[source_attributes[1].strip()] = {
            'payment_address': source_attributes[2].strip(),
            'amount': int(amount),
            'extra': int(extra)
        }
    return payment_sources
# End helper functions
