import binascii
import os
import struct


# https://github.com/Yelp/py_zipkin/blob/
# 7937ca859f8ae1f1009ab69fd1ddcd8fc33f1dad/py_zipkin/util.py#L1-L54
def generate_random_64bit_string() -> str:
    """Returns a 64 bit UTF-8 encoded string. In the interests of simplicity,
    this is always cast to a `str` instead of (in py2 land) a unicode string.
    Certain clients (I'm looking at you, Twisted) don't enjoy unicode headers.

    :returns: random 16-character string
    """
    return str(binascii.hexlify(os.urandom(8)).decode('utf-8'))


def generate_random_128bit_string() -> str:
    """Returns a 128 bit UTF-8 encoded string. Follows the same conventions
    as generate_random_64bit_string().

    :returns: random 32-character string
    """
    return str(binascii.hexlify(os.urandom(16)).decode('utf-8'))


def unsigned_hex_to_signed_int(hex_string: str) -> int:
    """Converts a 64-bit hex string to a signed int value.

    This is due to the fact that Apache Thrift only has signed values.

    Examples:
        '17133d482ba4f605' => 1662740067609015813
        'b6dbb1c2b362bf51' => -5270423489115668655

    :param hex_string: the string representation of a zipkin ID
    :returns: signed int representation
    """
    v: int = struct.unpack(
        'q', struct.pack('Q', int(hex_string, 16)))[0]
    return v


def signed_int_to_unsigned_hex(signed_int: int) -> str:
    """Converts a signed int value to a 64-bit hex string.

    Examples:
        1662740067609015813  => '17133d482ba4f605'
        -5270423489115668655 => 'b6dbb1c2b362bf51'

    :param signed_int: an int to convert
    :returns: unsigned hex string
    """
    hex_string = hex(struct.unpack('Q', struct.pack('q', signed_int))[0])[2:]
    if hex_string.endswith('L'):
        return hex_string[:-1]
    return hex_string
