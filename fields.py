class Type(object):
    def __init__(self, total_size):
        self.total_size = total_size

    def __eq__(self, other):
        if not isinstance(other, Type):
            return NotImplemented

        return self.total_size == other.total_size


class Void(Type):
    def __init__(self):
        super(Void, self).__init__(0)

    def __eq__(self, other):
        if not isinstance(other, Void):
            return NotImplemented

        return super(Void, self).__eq__(other)


class Bitfield(Type):
    def __init__(self, total_size):
        super(Bitfield, self).__init__(total_size)

    def __eq__(self, other):
        if not isinstance(other, Bitfield):
            return NotImplemented

        return super(Bitfield, self).__eq__(other)


class Scalar(Type):
    def __init__(self, total_size, type_):
        super(Scalar, self).__init__(total_size)
        self.type = type_

    def __eq__(self, other):
        print(self, other)
        if not isinstance(other, Scalar):
            return NotImplemented

        return self.type == other.type and super(Scalar, self).__eq__(other)


class StructField(Type):
    def __init__(self, total_size, type_):
        super(StructField, self).__init__(total_size)
        self.type = type_

    def __eq__(self, other):
        if not isinstance(other, StructField):
            return NotImplemented

        return self.type == other.type and super(StructField, self).__eq__(other)


class UnionField(Type):
    def __init__(self, total_size, type_):
        super(UnionField, self).__init__(total_size)
        self.type = type_

    def __eq__(self, other):
        if not isinstance(other, UnionField):
            return NotImplemented

        return self.type == other.type and super(UnionField, self).__eq__(other)


class Function(Type):
    def __init__(self, total_size, type_):
        super(Function, self).__init__(total_size, type_)
        self.type = type_

    def __eq__(self, other):
        if not isinstance(other, Function):
            return NotImplemented

        return super(Function, self).__eq__(other)


class Pointer(Type):
    def __init__(self, total_size, pointed_type):
        super(Pointer, self).__init__(total_size)
        self.pointed_type = pointed_type

    def __eq__(self, other):
        if not isinstance(other, Pointer):
            return NotImplemented

        return self.pointed_type == other.pointed_type and super(Pointer, self).__eq__(other)


class Array(Type):
    def __init__(self, total_size, num_elem, elem_type):
        super(Array, self).__init__(total_size)
        self.num_elem = num_elem
        self.elem_type = elem_type

    def __eq__(self, other):
        if not isinstance(other, Array):
            return NotImplemented

        return (self.num_elem == other.num_elem and self.elem_type == other.elem_type
                and super(Array, self).__eq__(other))
