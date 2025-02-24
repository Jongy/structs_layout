import os.path
import subprocess
import tempfile

from python.fields import (
    Scalar,
    Bitfield,
    Pointer,
    Void,
    Function,
    Array,
    StructField,
    Struct,
)


STRUCT_LAYOUT_SO = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "struct_layout.so")
)


def run_gcc(code_path, output_path, struct_name):
    args = [
        "gcc",
        "-fplugin={}".format(STRUCT_LAYOUT_SO),
        "-fplugin-arg-struct_layout-output={}".format(output_path),
    ]
    if struct_name:
        args.append("-fplugin-arg-struct_layout-struct={}".format(struct_name))
    args += ["-c", "-o", "/dev/null", "-x", "c", code_path]

    subprocess.check_call(args)


def dump_struct_layout(struct_code, struct_name):
    with tempfile.NamedTemporaryFile() as tf1, tempfile.NamedTemporaryFile("r") as tf2:
        tf1.write(struct_code.encode("ascii"))
        tf1.flush()

        run_gcc(tf1.name, tf2.name, struct_name)

        load_globals = {
            "Scalar": Scalar,
            "Bitfield": Bitfield,
            "Void": Void,
            "Function": Function,
            "StructField": StructField,
            "Pointer": Pointer,
            "Array": Array,
            "Struct": Struct,
        }
        struct_def = tf2.read()
        print(struct_def)  # for debugging
        # hehe :(
        exec(struct_def, load_globals)
        return load_globals["structs"]


def test_struct_basic():
    s = dump_struct_layout("struct x { int y; unsigned char z; };", "x")["x"].fields
    assert len(s.keys()) == 2
    assert s["y"] == (0, Scalar(32, "int", True))
    assert s["z"] == (32, Scalar(8, "unsigned char", False))


def test_struct_pointer():
    s = dump_struct_layout("struct x { void *p; void **h; const int ***z; };", "x")[
        "x"
    ].fields
    assert len(s.keys()) == 3
    assert s["p"] == (0, Pointer(64, Void()))
    assert s["h"] == (64, Pointer(64, Pointer(64, Void())))
    assert s["z"] == (
        128,
        Pointer(64, Pointer(64, Pointer(64, Scalar(32, "int", True)))),
    )


def test_struct_array():
    s = dump_struct_layout("struct x { int arr[5]; void *p[2]; };", "x")["x"].fields
    assert len(s.keys()) == 2
    assert s["arr"] == (0, Array(5 * 32, 5, Scalar(32, "int", True)))
    assert s["p"] == (5 * 32 + 32, Array(2 * 64, 2, Pointer(64, Void())))


def test_struct_array_two_dimensions():
    s = dump_struct_layout("struct x { int arr[5][2]; };", "x")["x"].fields
    assert len(s.keys()) == 1
    assert s["arr"] == (
        0,
        Array(5 * 2 * 32, 5, Array(2 * 32, 2, Scalar(32, "int", True))),
    )


def test_struct_array_flexible_and_zero():
    s = dump_struct_layout("struct x { int arr[0]; };", "x")["x"].fields
    assert len(s.keys()) == 1
    assert s["arr"] == (0, Array(0, 0, Scalar(32, "int", True)))

    # flexible array can't be the first field.
    s = dump_struct_layout("struct x { int y; int arr[]; };", "x")["x"].fields
    assert len(s.keys()) == 2
    assert s["y"] == (0, Scalar(32, "int", True))
    assert s["arr"] == (32, Array(0, 0, Scalar(32, "int", True)))


def test_struct_struct():
    s = dump_struct_layout(
        "struct a { int x; }; struct b { struct a aa; int xx; };", "b"
    )["b"].fields
    assert len(s.keys()) == 2
    assert s["aa"] == (0, StructField(32, "a"))
    assert s["xx"] == (32, Scalar(32, "int", True))


def test_struct_union():
    structs = dump_struct_layout(
        "union u { int x; signed char c; long l; }; struct c { union u u; };", "c"
    )

    c = structs["c"].fields
    assert len(c.keys()) == 1
    assert c["u"] == (0, StructField(64, "u"))

    u = structs["u"]
    assert u.total_size == 64
    u = u.fields
    assert len(u.keys()) == 3
    assert u["x"] == (0, Scalar(32, "int", True))
    # "signed" for stability across different arches where "char" has different signedness
    assert u["c"] == (0, Scalar(8, "signed char", True))
    assert u["l"] == (0, Scalar(64, "long int", True))


def test_struct_anonymous_union():
    s = dump_struct_layout("struct c { union { int x; float f; }; };", "c")["c"].fields
    assert len(s.keys()) == 2
    assert s["x"] == (0, Scalar(32, "int", True))
    assert s["f"] == (0, Scalar(32, "float", True))


def test_struct_recursive_dump():
    structs = dump_struct_layout("struct a { int x; }; struct b { struct a a; }; ", "b")

    b = structs["b"].fields
    assert len(b.keys()) == 1
    assert b["a"] == (0, StructField(32, "a"))

    a = structs[b["a"][1].type].fields
    assert len(a.keys()) == 1
    assert a["x"] == (0, Scalar(32, "int", True))


def test_struct_dump_only_necessary():
    structs = dump_struct_layout("struct a { int x; }; struct b { int y; };", "b")

    b = structs["b"].fields
    assert len(b.keys()) == 1
    assert b["y"] == (0, Scalar(32, "int", True))

    assert "a" not in structs


def test_struct_dump_all():
    decls = dump_struct_layout("struct a { int x; }; struct b { int y; };", None)

    b = decls["b"].fields
    assert len(b.keys()) == 1
    assert b["y"] == (0, Scalar(32, "int", True))

    b = decls["a"].fields
    assert len(b.keys()) == 1
    assert b["x"] == (0, Scalar(32, "int", True))


def test_struct_bitfields():
    x = dump_struct_layout(
        "struct x { int bf1: 3; int:5; int bf2: 1; int n; int bf3: 29; unsigned int bf4: 1; };",
        "x",
    )["x"].fields

    assert len(x.keys()) == 5
    assert x["bf1"] == (0, Bitfield(3, True))
    assert x["bf2"] == (8, Bitfield(1, True))
    assert x["n"] == (32, Scalar(32, "int", True))
    assert x["bf3"] == (64, Bitfield(29, True))
    assert x["bf4"] == (93, Bitfield(1, False))


def test_struct_function_ptrs():
    x = dump_struct_layout("struct x { int (*f)(int) };", "x")["x"].fields

    assert len(x.keys()) == 1
    assert x["f"] == (0, Pointer(64, Function()))


def test_struct_anonymous_enum():
    x = dump_struct_layout("struct x { enum { x = 5, } e; };", "x")["x"].fields

    assert len(x.keys()) == 1
    assert x["e"] == (0, Scalar(32, "anonymous enum", False))


def test_struct_typedefs():
    structs = dump_struct_layout(
        "struct s { int y; }; typedef struct s s_t; struct x { s_t s1; };", None
    )

    assert len(structs.keys()) == 2
    x = structs["x"].fields
    assert x["s1"] == (0, StructField(32, "s"))
    # not by typedef
    assert "s" in structs
    assert "s_t" not in structs

    structs = dump_struct_layout(
        "typedef struct { int y; } s_t; struct x { s_t s1; };", None
    )

    assert len(structs.keys()) == 2
    x = structs["x"].fields
    assert x["s1"] == (0, StructField(32, "s_t"))
    assert "s" not in structs
    assert "s_t" in structs

    # also for enums, they have special treatment
    x = dump_struct_layout("typedef enum { y = 1, } e_t; struct x { e_t e1; };", "x")[
        "x"
    ].fields
    assert x["e1"] == (0, Scalar(32, "e_t", False))

    x = dump_struct_layout("typedef enum e { y = 1, } e_t; struct x { e_t e1; };", "x")[
        "x"
    ].fields
    assert x["e1"] == (0, Scalar(32, "e", False))
