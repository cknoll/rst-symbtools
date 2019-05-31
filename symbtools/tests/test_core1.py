# -*- coding: utf-8 -*-
"""
Created on 2019-05-29 18:44:15 (copy from test_core)

@author: Carsten Knoll
"""


import sympy as sp
from sympy import sin, cos, exp

import numpy as np

import symbtools as st


try:
    import control
except ImportError:
    control = None

import unittest


# noinspection PyShadowingNames,PyPep8Naming,PySetFunctionToLiteral
class SymbToolsTest(unittest.TestCase):

    def setUp(self):
        st.init_attribute_store(reinit=True)

    def test_system_prolongation1(self):
        x1, x2, x3 = xx = st.symb_vector('x1:4')
        z1, z2, z3 = zz = st.symb_vector('z1:4')
        a1, a2, a3 = aa = st.symb_vector('a1:4')

        f = sp.Matrix([x2, 0, 0])
        gg = sp.Matrix([[0, 0], [a1, a2], [0, a3]])

        fnew, ggnew, xxnew = st.system_pronlongation(f, gg, xx, [(0, 2), (1, 1)])

        fnew_ref = sp.Matrix([x2, a1*z1 + a2*z3, a3*z3,  z2, 0, 0])
        ggnew_ref = sp.eye(6)[:, -2:]

        self.assertEqual(fnew, fnew_ref)
        self.assertEqual(ggnew, ggnew_ref)

    def test_system_prolongation2(self):
        # test the avoidance of name collisions

        x1, x2, x3 = xx = st.symb_vector('x1:4')
        z1, z2, z3 = zz = st.symb_vector('z1:4')
        z4, z5, z6 = ZZ = st.symb_vector('z4:7')
        a1, a2, a3 = aa = st.symb_vector('a1:4')

        f = sp.Matrix([x2, x1*z3, 0])
        gg = sp.Matrix([[0, 0], [a1, a2], [0, a3]])

        XX = [x1, x2, z3]

        fnew, ggnew, xxnew = st.system_pronlongation(f, gg, XX, [(0, 2), (1, 1)])

        fnew_ref = sp.Matrix([x2, z3*x1 + a1*z4 + a2*z6, a3*z6,  z5, 0, 0])
        ggnew_ref = sp.eye(6)[:, -2:]

        self.assertEqual(fnew, fnew_ref)
        self.assertEqual(ggnew, ggnew_ref)

    def test_depends_on_t1(self):
        a, b, t = sp.symbols("a, b, t")
        A = sp.Function("A")

        res1 = st.depends_on_t(a+b, t, [])
        self.assertEqual(res1, False)

        res2 = st.depends_on_t(a + b, t, [a,])
        self.assertEqual(res2, True)

        res3 = st.depends_on_t(A(t) + b, t, [])
        self.assertEqual(res3, True)

        res4 = st.depends_on_t(A(t) + b, t, [b])
        self.assertEqual(res4, True)

        res5 = st.depends_on_t(t, t, [])
        self.assertEqual(res5, True)

        adot = st.time_deriv(a, [a])
        res5 = st.depends_on_t(adot, t, [])
        self.assertEqual(res5, True)

        x1, x2 = xx = sp.symbols("x1, x2")
        x1dot = st.time_deriv(x1, xx)
        self.assertTrue(st.depends_on_t(x1dot, t))

        y1, y2 = yy = sp.Matrix(sp.symbols("y1, y2", commutative=False))
        yydot = st.time_deriv(yy, yy, order=1, commutative=False)
        self.assertTrue(st.depends_on_t(yydot, t))

    def test_symbs_to_func1(self):
        a, b, t = sp.symbols("a, b, t")
        x = a + b
        # M = sp.Matrix([x, t, a**2])

        f_x = st.symbs_to_func(x, [a, b], t)
        self.assertEqual(str(f_x), "a(t) + b(t)")

    def test_perform_time_deriv1(self):
        a, b, t = sp.symbols("a, b, t")
        f1 = a**2 + 10*sin(b)
        f1_dot = st.time_deriv(f1, (a, b))
        self.assertEqual(str(f1_dot), "2*a*adot + 10*bdot*cos(b)")

        f2 = sin(a)
        f2_dot2 = st.time_deriv(f2, [a, b], order=2)
        f2_dot = st.time_deriv(f2, [a])
        f2_ddot = st.time_deriv(f2_dot, [a, sp.Symbol('adot')])
        self.assertEqual(f2_ddot, f2_dot2)

    def test_perform_time_deriv2(self):
        """
        test matrix compatibility
        """

        a, b, t = sp.symbols("a, b, t")
        x, y = sp.symbols("x, y")

        adot, bdot = st.time_deriv( sp.Matrix([a, b]), (a, b) )

        self.assertEqual(a.ddt_child, adot)
        self.assertEqual(bdot.ddt_parent, b)

        A = sp.Matrix([sin(a), exp(a*b), -t**2*7*0, x + y]).reshape(2, 2)
        A_dot = st.time_deriv(A, (a, b))

        A_dot_manual = \
            sp.Matrix([adot*cos(a), b*adot*exp(a*b) + a*bdot*exp(a*b),
                       -t**2*7*0, 0]).reshape(2, 2)

        self.assertEqual(A_dot.expand(), A_dot_manual)

    def test_perform_time_deriv3(self):
        """
        test to provide deriv_symbols
        """

        a, b, adot, bdot, addot, bddot = sp.symbols("a, b, adot, bdot, addot, bddot")

        f1 = 8*a*b**2
        f1d = st.time_deriv(f1, (a, b), (adot, bdot))
        self.assertEqual(f1d, 8*adot*b**2 + 16*a*bdot*b)

        f1d_2 = st.time_deriv(f1, (a, b), (adot, bdot)+ (addot, bddot),
                                           order=2)

        f1d_2_altntv = st.time_deriv(f1d, (a, b, adot, bdot),
                                                 (adot, bdot)+ (addot, bddot) )
        self.assertEqual(sp.expand(f1d_2 - f1d_2_altntv), 0)

    def test_perform_time_deriv4(self):
        # test higher order derivatives

        a, b = sp.symbols("a, b")

        f1 = 8*a*b**2

        res_a1 = st.time_deriv(f1, (a, b), order=5)

        a_str = 'a adot addot adddot addddot a_d5'
        b_str = a_str.replace('a', 'b')

        expected_symbol_names = a_str.split() + b_str.split()

        res_list = [res_a1.has(sp.Symbol(e)) for e in expected_symbol_names]

        self.assertTrue( all(res_list) )

        l1 = len( res_a1.atoms(sp.Symbol) )
        self.assertEqual(len(expected_symbol_names), l1)

    def test_perform_time_deriv5(self):
        # test numbered symbols

        x1, x2 = xx = sp.symbols("x1, x_2")

        res_a1 = st.time_deriv(x1, xx)
        self.assertEqual(str(res_a1), 'xdot1')

        res_a2 = st.time_deriv(x1, xx, order=2)
        self.assertEqual(str(res_a2), 'xddot1')

        res_a3 = st.time_deriv(x1, xx, order=3)
        self.assertEqual(str(res_a3), 'xdddot1')

        res_a4 = st.time_deriv(x1, xx, order=4)
        self.assertEqual(str(res_a4), 'xddddot1')

        # FIXME:
        res_a5 = st.time_deriv(x1, xx, order=5)
        # self.assertEqual(str(res_a5), 'x1_d5')

        # test attributes ddt_child and ddt_parent
        tmp = x1
        for i in range(res_a5.difforder):
            tmp = tmp.ddt_child
        self.assertEqual(tmp, res_a5)

        tmp = res_a5
        for i in range(res_a5.difforder):
            tmp = tmp.ddt_parent
        self.assertEqual(tmp, x1)

        self.assertEqual(st.time_deriv(x1.ddt_child, xx, order=2),
                         x1.ddt_child.ddt_child.ddt_child)

        res_b1 = st.time_deriv(x2, xx)
        self.assertEqual(str(res_b1), 'x_dot2')

        res_b2 = st.time_deriv(x2, xx, order=2)
        self.assertEqual(str(res_b2), 'x_ddot2')

        res_b3 = st.time_deriv(x2, xx, order=3)
        self.assertEqual(str(res_b3), 'x_dddot2')

        res_b4 = st.time_deriv(x2, xx, order=4)
        self.assertEqual(str(res_b4), 'x_ddddot2')

        # FIXME
        res_b5 = st.time_deriv(x2, xx, order=5)
        # self.assertEqual(str(res_b5), 'x_2_d5')

    @unittest.expectedFailure
    def test_perform_time_deriv5f(self):
        # test numbered symbols

        x1, x2 = xx = sp.symbols("x1, x_2")

        # TODO: These two assertions should pass
        # Then the above FIXME-issues can be resolved and this test is obsolete

        res_a5 = st.time_deriv(x1, xx, order=5)
        self.assertEqual(str(res_a5), 'x1_d5')

        res_b5 = st.time_deriv(x2, xx, order=5)
        self.assertEqual(str(res_b5), 'x_2_d5')

    def test_time_deriv7(self):
        a, b, t = sp.symbols("a, b, t", commutative=False)

        f1 = sp.Function('f1')(t)
        f2 = sp.Function('f2')(t)

        res1 = st.time_deriv(f1, [a])
        self.assertEqual(res1, f1.diff(t))

        res2 = st.time_deriv(f1, [])
        self.assertEqual(res2, f1.diff(t))

        res3 = st.time_deriv(a*f1, [a, b])
        adot = st.time_deriv(a, [a])
        self.assertEqual(res3, a*f1.diff(t) + adot*f1)

    def test_time_deriv8(self):

        y1, y2 = yy = sp.Matrix( sp.symbols('y1, y2', commutative=False) )

        ydot1 = st.time_deriv(y1, yy)
        ydot2 = st.time_deriv(y2, yy)

        yddot1 = st.time_deriv(y1, yy, order=2)
        ydddot1 = st.time_deriv(y1, yy, order=3)

        res1 = st.time_deriv(ydot1, yy)
        self.assertEqual(res1, yddot1)

        res2 = st.time_deriv(ydot1, yy, order=2)
        self.assertEqual(res2, ydddot1)

        res3 = st.time_deriv(yddot1, yy)
        self.assertEqual(res3, ydddot1)

    def test_time_deriv_matrix_symbol1(self):
        A = sp.MatrixSymbol("A", 3, 3)
        B = sp.MatrixSymbol("B", 3, 5)
        C = sp.MatrixSymbol("C", 5, 5)

        Adot = st.time_deriv(A, [A])
        Cdot = st.time_deriv(C, [C])

        self.assertEqual(Adot.shape, A.shape)
        self.assertEqual(Adot.name, "Adot")

        res1 = st.time_deriv(3*A, [A])
        self.assertEqual(res1, 3*Adot)

        res2 = st.time_deriv(A*B*C, [A])
        self.assertEqual(res2, Adot*B*C)

        res3 = st.time_deriv(A*B*C + B*C, [A, C])
        self.assertEqual(res3, B*Cdot + A*B*Cdot + Adot*B*C)

    def test_time_deriv_matrix_symbol2(self):
        A = sp.MatrixSymbol("A", 3, 3)
        B = sp.MatrixSymbol("B", 3, 5)
        C = sp.MatrixSymbol("C", 5, 5)

        # test higher order

        Adot = st.time_deriv(A, [A])
        Cdot = st.time_deriv(C, [C])

        Addot = st.time_deriv(A, [A], order=2)
        Cddot = st.time_deriv(C, [C], order=2)

        Adddot = st.time_deriv(A, [A], order=3)
        Cdddot = st.time_deriv(C, [C], order=3)

        Addddot = st.time_deriv(A, [A], order=4)
        Cddddot = st.time_deriv(C, [C], order=4)

        self.assertEqual(Addddot.shape, A.shape)
        self.assertEqual(Addddot.name, "Addddot")

        res1 = st.time_deriv(3*A, [A], order=3)
        self.assertEqual(res1, 3*Adddot)

        res2 = st.time_deriv(A*B*C, [A], order=2)
        self.assertEqual(res2, Addot*B*C)

        res3 = st.time_deriv(A*B*C + B*C, [A, C], order=4)
        eres3 = B*Cddddot + A*B*Cddddot + Addddot*B*C + 4*Adddot*B*Cdot + \
                   4*Adot*B*Cdddot + 6*Addot*B*Cddot
        self.assertEqual(res3, eres3)

        res4 = st.time_deriv(Adot, [A]) - Addot
        self.assertEqual(res4, 0*A)

        res5 = st.time_deriv(Adot, [A], order=3)
        self.assertEqual(res5, Addddot)

        res6 = st.time_deriv(A*B, [A], order=0)
        self.assertEqual(res6, A*B)

    def test_dynamic_time_deriv1(self):

        x1, x2 = xx = st.symb_vector("x1, x2")
        u1, u2 = uu = st.symb_vector("u1, u2")

        uu_dot = st.time_deriv(uu, uu)
        uu_ddot = st.time_deriv(uu, uu, order=2)

        ff = sp.Matrix([x2 + sp.exp(3*x1), x1**2])
        GG = sp.Matrix([[x1 - x1**2*x2, sin(x1/x2)], [1 , x1**2 + x2]])
        FF = ff + GG*uu

        h = x1*cos(x2)
        h_dot_v1 = st.dynamic_time_deriv(h, FF, xx, uu)
        h_dot_v2 = st.lie_deriv(h, FF, xx)
        self.assertEqual(h_dot_v1, h_dot_v2)

        h_dddot_v1 = st.dynamic_time_deriv(h, FF, xx, uu, order=3)
        h_ddot_v2 = st.dynamic_time_deriv(h_dot_v1, FF, xx, uu)
        h_dddot_v2 = st.dynamic_time_deriv(h_ddot_v2, FF, xx, uu)

        self.assertEqual(h_dddot_v1, h_dddot_v2)

        self.assertTrue(uu[0] in h_dot_v1.atoms())
        self.assertTrue(uu_dot[0] in h_ddot_v2.atoms())
        self.assertTrue(uu_dot[0] in h_dddot_v1.atoms())

    def test_dynamic_time_deriv2(self):

        x1, x2 = xx = st.symb_vector("x1, x2")
        u1, u2 = uu = st.symb_vector("u1, u2")
        uu_dot = st.time_deriv(uu, uu)

        ff = sp.Matrix([x2 + sp.exp(3*x1), x1**2])
        GG = sp.Matrix([[x1 - x1**2*x2, sin(x1/x2)], [1, x1**2 + x2]])
        FF = ff + GG*uu

        H = sp.Matrix([[x1, cos(x2)], [sp.exp(x1*x2), 4]])

        H_ddot = st.dynamic_time_deriv(H, FF, xx, uu, order=2)

        self.assertEqual(H.shape, H_ddot.shape)

        h11 = H[1, 1]

        h11_dot = st.lie_deriv(h11, FF, xx)
        h11_ddot = st.lie_deriv(h11_dot, FF, xx)
        h11_ddot += h11_dot.diff(u1)*uu_dot[0] + h11_dot.diff(u2)*uu_dot[1]
        self.assertEqual(H_ddot[1, 1], h11_ddot)

    def test_get_all_deriv_childs(self):

        x1, x2 = xx = st.symb_vector("x1, x2")

        expr = x1*x2

        E2 = st.time_deriv(expr, xx, order=2)

        dc = st.get_all_deriv_childs(xx)

        self.assertEqual(len(dc), 4)

        xdot1, xdot2 = st.time_deriv(xx, xx)
        xddot1, xddot2 = st.time_deriv(xx, xx, order=2)

        self.assertTrue( xdot1 in dc)
        self.assertTrue( xddot1 in dc)
        self.assertTrue( xdot2 in dc)
        self.assertTrue( xddot2 in dc)

    # TODO: move to TestSupportFunctions
    def test_match_symbols_by_name(self):
        a, b, c = abc0 = sp.symbols('a5, b, c', real=True)
        a1, b1, c1 = abc1 = sp.symbols('a5, b, c')

        self.assertFalse(a == a1 or b == b1 or c == c1)

        abc2 = st.match_symbols_by_name(abc0, abc1)
        self.assertEqual(abc0, tuple(abc2))

        input3 = [a1, b, "c", "x"]
        res = st.match_symbols_by_name(abc0, input3, strict=False)
        self.assertEqual(abc0, tuple(res))

        with self.assertRaises(ValueError) as cm:
            res = st.match_symbols_by_name(abc0, input3)  # implies strict=True

        err = cm.exception
        if hasattr(err, 'args'):
            msg = err.args[0]
        else:
            msg = err.message
        self.assertTrue('symbol x' in msg)

        self.assertEqual(abc0, tuple(res))

        r = st.match_symbols_by_name(abc0, 'a5')
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0], a)

        # test expression as first argument

        expr = a*b**c + 5
        r3 = st.match_symbols_by_name(expr, ['c', 'a5'])
        self.assertEqual(r3, [c, a])

    def test_symbs_to_func2(self):
        a, b, t = sp.symbols("a, b, t")
        x, y = sp.symbols("x, y")

        at = sp.Function('a')(t)
        bt = sp.Function('b')(t)

        xt = sp.Function('x')(t)
        yt = sp.Function('y')(t)

        M = sp.Matrix([x, y])
        Mt = sp.Matrix([xt, yt])

        expr1 = a**2 + b**2
        f1 = st.symbs_to_func(expr1, (a,b), t)
        self.assertEqual(f1, at**2 + bt**2)

        at2 = st.symbs_to_func(a, arg=t)
        self.assertEqual(at, at2)

        # Matrix
        Mt2 = st.symbs_to_func(M, arg=t)
        self.assertEqual(Mt, Mt2)

        # TODO: assert raises

    def test_poly_expr_coeffs(self):
        a, b, c, d = sp.symbols("a, b, c, d")
        x, y = sp.symbols("x, y")

        p1 = a*x + b*x**2 + c*y - d + 2*a*x*y
        sample_solution = [((0, 0), -d), ((1, 0), a), ((2, 0), b),
                           ((0, 1), c), ((1, 1), 2*a), ((0, 2), 0)]

        # coeff-dict
        cd1 = st.poly_expr_coeffs(p1, [x,y])
        self.assertEqual(cd1, dict(sample_solution))

    def test_get_diffterms(self):
        x1, x2, x3, = xx = sp.symbols('x1:4')
        res2 = st.get_diffterms(xx, 2)
        expected_res2 = [(x1, x1), (x1, x2), (x1, x3), (x2, x2),
                         (x2, x3), (x3, x3)]

        expected_indices2 = [(2, 0, 0), (1, 1, 0), (1, 0, 1), (0, 2, 0),
                             (0, 1, 1), (0, 0, 2)]
        self.assertEqual(res2, expected_res2)

        res3 = st.get_diffterms(xx, 3)
        res23 = st.get_diffterms(xx, (2, 3))

        self.assertEqual(res23, res2 + res3)

        res2b, indices2 = st.get_diffterms(xx, 2, order_list=True)
        self.assertEqual(res2b, res2)
        self.assertEqual(expected_indices2, indices2)

        res3b, indices3 = st.get_diffterms(xx, 3, order_list=True)
        res23b, indices23 = st.get_diffterms(xx, (2, 3), order_list=True)

        self.assertEqual(res23b, res2b + res3b)
        self.assertEqual(indices23, indices2 + indices3)

    def test_get_diffterms_bug1(self):
        xx = sp.symbols('x, y')
        res, orders = st.get_diffterms(xx, 2, order_list=True)
        self.assertEqual(orders, [(2, 0), (1, 1), (0, 2)])

    def test_monomial_from_signature(self):
        x1, x2, x3, = xx = sp.symbols('x1:4')

        s1 = (0, 0, 0)
        p1 = st.monomial_from_signature(s1, xx)
        self.assertEqual(p1, 1)

        s2 = (3, 2, 1)
        p2 = st.monomial_from_signature(s2, xx)
        self.assertEqual(p2, x1**3 * x2**2 * x3 )

    def test_zip0(self):
        aa = sp.symbols('a1:5')
        bb = sp.symbols('b1:4')
        xx = sp.symbols('x1:3')

        s1 = sum(aa)
        self.assertEqual(s1.subs(st.zip0(aa)), 0)
        self.assertEqual(s1.subs(st.zip0(aa, arg=3.5)), 3.5*len(aa))
        self.assertEqual(s1.subs(st.zip0(aa, arg=xx[0])), xx[0]*len(aa))

        s2 = s1 + sum(bb) + sum(xx)
        self.assertEqual(s1.subs(st.zip0(aa, bb, xx)), 0)
        t2 = s2.subs(st.zip0(aa, bb, xx, arg=-2.1))
        self.assertEqual( t2, -2.1*len(aa + bb + xx) )

        ff = sp.Function('f1')(*xx), sp.Function('f2')(*xx)
        s3 = ff[0] + ff[1] + 10

        # noinspection PyUnresolvedReferences
        self.assertEqual( s3.subs(st.zip0(ff)), 10 )

    def test_is_number(self):
        x1, x2, x3 = xx = sp.symbols('x1:4')

        self.assertTrue(st.is_number(x1/x1))
        self.assertTrue(st.is_number(1))
        self.assertTrue(st.is_number(3.4))
        self.assertTrue(st.is_number(-10.0000001))

        z = sp.Rational('0.019914856674816989123456787654321').evalf(40)
        self.assertTrue(st.is_number(z))

        self.assertFalse(st.is_number(x1))
        self.assertFalse(st.is_number(x1/x2))
        self.assertFalse(st.is_number(float('nan')))
        self.assertFalse(st.is_number(float('inf')))
        self.assertFalse(st.is_number(-float('inf')))

        self.assertTrue(st.is_number(7.5 - 23j, allow_complex=True))
        self.assertTrue(st.is_number(np.pi*1j + np.exp(1), allow_complex=True) )
        self.assertFalse(st.is_number(np.pi*1j + np.exp(1)))

    def test_deriv_2nd_order_chain_rule(self):
        a, b, x = sp.symbols('a, b, x')

        f1 = a**3 + a*b**2 + 7*a*b
        f2 = -2*a**2 + b*a*b**2/(2+a**2 * b**2) + 12*a*b
        f3 = -3*a**2 + b*a*b**2 + 7*a*b/(2+a**2 * b**2)

        f = f1
        aa = sp.cos(3*x)
        bb = sp.exp(5*x)

        ab_subs = [(a, aa), (b, bb)]
        fab = f.subs(ab_subs)
        fab_d2 = fab.diff(x, 2)

        res1 = st.deriv_2nd_order_chain_rule(f, (a,b), [aa, bb], x)

        res1a = sp.simplify(res1 - fab_d2)
        self.assertEqual(res1a, 0)

        # multiple functions

        ff = sp.Matrix([f1, f2, f3])

        ff_ab_d2 = ff.subs(ab_subs).diff(x, 2)

        res2 = st.deriv_2nd_order_chain_rule(ff, (a, b), [aa, bb], x)
        res2a = sp.expand(res2 - ff_ab_d2)
        self.assertEqual(res2a, res2a*0)

    def test_update_cse(self):
        a, b, c, x1, x2, x3 = sp.symbols('a, b, c, x1, x2, x3')

        L1 = [(x1, a + b), (x2, x1*b**2)]
        new_subs1 = [(b, 2)]
        new_subs2 = [(a, b + 5), (b, 3),]

        res1_exp = [(x1, a + 2), (x2, (a + 2)*4)]
        res2_exp = [(x1, 11), (x2, 99)]

        res1 = st.update_cse(L1, new_subs1)
        res2 = st.update_cse(L1, new_subs2)

        self.assertEqual(res1, res1_exp)
        self.assertEqual(res2, res2_exp)

    def test_solve_linear_system1(self):
        M = sp.randMatrix(3, 8, seed=1131)
        xx = sp.Matrix(sp.symbols('x1:9'))
        bb = sp.Matrix(sp.symbols('b1:4'))

        eqns = M*xx + bb

        sol1 = sp.solve(eqns, xx)
        sol2 = st.solve_linear_system(eqns, xx)

        self.assertEqual(xx.subs(sol1) - xx.subs(sol2), xx*0)

        # symbolic coefficient matrix
        # this is (currently) not possible with sp.solve
        # (additionally add a zero line)
        M2 = st.symbMatrix(4, 8)
        bb2 = sp.Matrix(sp.symbols('b1:5'))
        eqns = M2*xx + bb2

        eqns[-1, :] *= 0
        sol3 = st.solve_linear_system(eqns, xx)

        res = eqns.subs(sol3)
        res.simplify()

        self.assertEqual(res, res*0)

    def test_solve_linear_system2(self):
        par = sp.symbols('phi0, phi1, phi2, phidot0, phidot1, phidot2, phiddot0, phiddot1,'
                         'phiddot2, m0, m1, m2, l0, l1, l2, J0, J1, J2, L1, L2')

        phi0, phi1, phi2, phidot0, phidot1, phidot2, phiddot0, phiddot1, \
        phiddot2, m0, m1, m2, l0, l1, l2, J0, J1, J2, L1, L2 = par

        k1, k2, k3, k4, k5, k6 = kk = sp.symbols('k1:7')

        eqns = sp.Matrix([[L1*l0*m2*sin(phi1) + k1*(-2*l2*m2*phidot2*(L1*sin(phi1 - phi2) -
                           l0*sin(phi2))*(J1 + L1**2*m2 + L1*l0*m2*cos(phi1) +
                           L1*l2*m2*cos(phi1 - phi2) + l0*l1*m1*cos(phi1) + l1**2*m1) -
                           2*phidot1*(L1*l0*m2*sin(phi1) + L1*l2*m2*sin(phi1 - phi2) +
                           l0*l1*m1*sin(phi1))*(J2 + L1*l2*m2*cos(phi1 - phi2) + l0*l2*m2*cos(phi2) +
                           l2**2*m2) - 2*(-L1*l0*m2*phidot1*sin(phi1) - L1*l2*m2*(phidot1 -
                           phidot2)*sin(phi1 - phi2) - l0*l1*m1*phidot1*sin(phi1))*(J2 + L1*l2*m2*cos(phi1 - phi2) +
                           l0*l2*m2*cos(phi2) + l2**2*m2)) - k2*(-2*l2*m2*phidot2*(L1*sin(phi1 - phi2) -
                           l0*sin(phi2))*(J0 + l0**2*m0 + l0*m1*(l0 + l1*cos(phi1)) + l0*m2*(L1*cos(phi1) +
                           l0 + l2*cos(phi2))) - 2*(-l0*l1*m1*phidot1*sin(phi1) + l0*m2*(-L1*phidot1*sin(phi1) - l2*phidot2*sin(phi2)))*(J2 + L1*l2*m2*cos(phi1 - phi2) + l0*l2*m2*cos(phi2) + l2**2*m2)) + k4*(J1 + L1**2*m2 + L1*l0*m2*cos(phi1) + L1*l2*m2*cos(phi1 - phi2) + l0*l1*m1*cos(phi1) + l1**2*m1) - k5*(J0 + l0**2*m0 + l0*m1*(l0 + l1*cos(phi1)) + l0*m2*(L1*cos(phi1) + l0 + l2*cos(phi2))) + l0*l1*m1*sin(phi1)],
                          [-2*k1*(-L1*l2*m2*(phidot1 - phidot2)*sin(phi1 - phi2) - l0*l2*m2*phidot2*sin(phi2))*(J2 + L1*l2*m2*cos(phi1 - phi2) + l0*l2*m2*cos(phi2) + l2**2*m2) - k3*(-2*l2*m2*phidot2*(L1*sin(phi1 - phi2) - l0*sin(phi2))*(J0 + l0**2*m0 + l0*m1*(l0 + l1*cos(phi1)) + l0*m2*(L1*cos(phi1) + l0 + l2*cos(phi2))) - 2*(-l0*l1*m1*phidot1*sin(phi1) + l0*m2*(-L1*phidot1*sin(phi1) - l2*phidot2*sin(phi2)))*(J2 + L1*l2*m2*cos(phi1 - phi2) + l0*l2*m2*cos(phi2) + l2**2*m2)) + k4*(J2 + L1*l2*m2*cos(phi1 - phi2) + l0*l2*m2*cos(phi2) + l2**2*m2) - k6*(J0 + l0**2*m0 + l0*m1*(l0 + l1*cos(phi1)) + l0*m2*(L1*cos(phi1) + l0 + l2*cos(phi2))) + l0*l2*m2*sin(phi2)]])

        sol_subs = st.solve_linear_system(eqns, kk)

        res = eqns.subs(sol_subs)
        res.simplify()

        self.assertEqual(res, res*0)

    def test_integrate_with_time_derivs(self):
        t = sp.Symbol("t")
        x1, x2 = xx = st.symb_vector("x1, x2")
        xdot1, xdot2 = xxd = st.time_deriv(xx, xx)

        z = xdot1 - 4*xdot2

        res = sp.integrate(z, t)

        self.assertEqual(res, x1 - 4 * xdot2)
