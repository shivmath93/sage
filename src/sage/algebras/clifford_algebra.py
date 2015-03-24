r"""
Clifford Algebras

AUTHORS:

- Travis Scrimshaw (2013-09-06): Initial version
"""

#*****************************************************************************
#  Copyright (C) 2013 Travis Scrimshaw <tscrim at ucdavis.edu>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.misc.cachefunc import cached_method
from sage.structure.unique_representation import UniqueRepresentation
from copy import copy

from sage.categories.algebras_with_basis import AlgebrasWithBasis
from sage.categories.hopf_algebras_with_basis import HopfAlgebrasWithBasis
from sage.categories.modules_with_basis import ModuleMorphismByLinearity
from sage.categories.poor_man_map import PoorManMap
from sage.rings.all import ZZ
from sage.modules.free_module import FreeModule, FreeModule_generic
from sage.matrix.constructor import Matrix
from sage.matrix.matrix_space import MatrixSpace
from sage.sets.family import Family
from sage.combinat.free_module import CombinatorialFreeModule
from sage.combinat.subset import SubsetsSorted
from sage.quadratic_forms.quadratic_form import QuadraticForm
from sage.algebras.weyl_algebra import repr_from_monomials

class CliffordAlgebraElement(CombinatorialFreeModule.Element):
    """
    An element in a Clifford algebra.

    TESTS::

        sage: Q = QuadraticForm(ZZ, 3, [1, 2, 3, 4, 5, 6])
        sage: Cl.<x,y,z> = CliffordAlgebra(Q)
        sage: elt = ((x^3-z)*x + y)^2
        sage: TestSuite(elt).run()
    """
    def _repr_(self):
        """
        Return a string representation of ``self``.

        TESTS::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: ((x^3-z)*x + y)^2
            -2*x*y*z - x*z + 5*x - 4*y + 2*z + 2
            sage: Cl.zero()
            0
        """
        return repr_from_monomials(self.list(), self.parent()._repr_term)

    def _latex_(self):
        r"""
        Return a `\LaTeX` representation of ``self``.

        TESTS::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: latex( ((x^3-z)*x + y)^2 )
            -2  x y z -  x z + 5  x - 4  y + 2  z + 2
            sage: Cl.<x0,x1,x2> = CliffordAlgebra(Q)
            sage: latex(  (x1 - x2)*x0 + 5*x0*x1*x2 )
            5  x_{0} x_{1} x_{2} -  x_{0} x_{1} +  x_{0} x_{2} - 1
        """
        return repr_from_monomials(self.list(), self.parent()._latex_term, True)

    def _mul_(self, other):
        """
        Return ``self`` multiplied by ``other``.

        INPUT:

        - ``other`` -- element of the same Clifford algebra as ``self``

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: (x^3 - z*y)*x*(y*z + x*y*z)
            x*y*z + y*z - 24*x + 12*y + 2*z - 24
            sage: y*x
            -x*y + 2
            sage: z*x
            -x*z + 3
            sage: z*z
            6
            sage: x*0
            0
            sage: 0*x
            0
        """
        Q = self.parent()._quadratic_form
        zero = self.parent().base_ring().zero()
        d = {}

        for ml,cl in self:
            # Distribute the current term ``cl`` * ``ml`` over ``other``.
            cur = copy(other._monomial_coefficients) # The current distribution of the term
            for i in reversed(ml):
                # Distribute the current factor ``e[i]`` (the ``i``-th
                # element of the standard basis).
                next = {}
                # At the end of the following for-loop, ``next`` will be
                # the dictionary describing the element
                # ``e[i]`` * (the element described by the dictionary ``cur``)
                # (where ``e[i]`` is the ``i``-th standard basis vector).
                for mr,cr in cur.iteritems():
                    # Commute the factor as necessary until we are in order
                    pos = 0
                    for j in mr:
                        if i <= j:
                            break
                        # Add the additional term from the commutation
                        t = list(mr)
                        t.pop(pos)
                        t = tuple(t)
                        next[t] = next.get(t, zero) + cr * Q[i,j]
                        # Note: ``Q[i,j] == Q(e[i]+e[j]) - Q(e[i]) - Q(e[j])`` for
                        # ``i != j``, where ``e[k]`` is the ``k``-th standard
                        # basis vector.
                        cr = -cr
                        if next[t] == zero:
                            del next[t]
                        pos += 1

                    # Check to see if we have a squared term or not
                    t = list(mr)
                    if i in t:
                        t.remove(i)
                        cr *= Q[i,i]
                        # Note: ``Q[i,i] == Q(e[i])`` where ``e[i]`` is the
                        # ``i``-th standard basis vector.
                    else:
                        t.insert(pos, i)
                        # Note that ``t`` is now sorted.
                    t = tuple(t)
                    next[t] = next.get(t, zero) + cr
                    if next[t] == zero:
                        del next[t]
                cur = next

            # Add the distributed terms to the total
            for index,coeff in cur.iteritems():
                d[index] = d.get(index, zero) + cl * coeff
                if d[index] == zero:
                    del d[index]

        return self.__class__(self.parent(), d)

    def list(self):
        """
        Return the list of monomials and their coefficients in ``self``
        (as a list of `2`-tuples, each of which has the form
        ``(monomial, coefficient)``).

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: elt = 5*x + y
            sage: elt.list()
            [((0,), 5), ((1,), 1)]
        """
        return sorted(self._monomial_coefficients.items(), key=lambda (m,c) : (-len(m), m))

    def support(self):
        """
        Return the support of ``self``.

        This is the list of all monomials which appear with nonzero
        coefficient in ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: elt = 5*x + y
            sage: elt.support()
            [(0,), (1,)]
        """
        return sorted(self._monomial_coefficients.keys(), key=lambda x: (-len(x), x))

    def reflection(self):
        """
        Return the image of the reflection automorphism on ``self``.

        The *reflection automorphism* of a Clifford algebra is defined
        as the linear endomorphism of this algebra which maps

        .. MATH::

            x_1 \wedge x_2 \wedge \cdots \wedge x_m \mapsto
            (-1)^m x_1 \wedge x_2 \wedge \cdots \wedge x_m.

        It is an algebra automorphism of the Clifford algebra.

        :meth:`degree_negation` is an alias for :meth:`reflection`.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: elt = 5*x + y + x*z
            sage: r = elt.reflection(); r
            x*z - 5*x - y
            sage: r.reflection() == elt
            True

        TESTS:

        We check that the reflection is an involution::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: all(x.reflection().reflection() == x for x in Cl.basis())
            True
        """
        return self.__class__(self.parent(), {m: (-1)**len(m) * c for m,c in self})

    degree_negation = reflection

    def transpose(self):
        r"""
        Return the transpose of ``self``.

        The transpose is an anti-algebra involution of a Clifford algebra
        and is defined (using linearity) by

        .. MATH::

            x_1 \wedge x_2 \wedge \cdots \wedge x_m \mapsto
            x_m \wedge \cdots \wedge x_2 \wedge x_1.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: elt = 5*x + y + x*z
            sage: t = elt.transpose(); t
            -x*z + 5*x + y + 3
            sage: t.transpose() == elt
            True
            sage: Cl.one().transpose()
            1

        TESTS:

        We check that the transpose is an involution::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: all(x.transpose().transpose() == x for x in Cl.basis())
            True

        Zero is sent to zero::

            sage: Cl.zero().transpose() == Cl.zero()
            True
        """
        P = self.parent()
        if not self._monomial_coefficients:
            return P.zero()
        g = P.gens()
        return P.sum(c * P.prod(g[i] for i in reversed(m)) for m,c in self)

    def conjugate(self):
        r"""
        Return the Clifford conjugate of ``self``.

        The Clifford conjugate of an element `x` of a Clifford algebra is
        defined as

        .. MATH::

            \bar{x} := \alpha(x^t) = \alpha(x)^t

        where `\alpha` denotes the :meth:`reflection <reflection>`
        automorphism and `t` the :meth:`transposition <transpose>`.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: elt = 5*x + y + x*z
            sage: c = elt.conjugate(); c
            -x*z - 5*x - y + 3
            sage: c.conjugate() == elt
            True

        TESTS:

        We check that the conjugate is an involution::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: all(x.conjugate().conjugate() == x for x in Cl.basis())
            True
        """
        return self.reflection().transpose()

    clifford_conjugate = conjugate

    # TODO: This is a general function which should be moved to a
    #   superalgebras category when one is implemented.
    def supercommutator(self, x):
        """
        Return the supercommutator of ``self`` and ``x``.

        Let `A` be a superalgebra. The *supercommutator* of homogeneous
        elements `x, y \in A` is defined by

        .. MATH::

            [x, y\} = x y - (-1)^{|x| |y|} y x

        and extended to all elements by linearity.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: a = x*y - z
            sage: b = x - y + y*z
            sage: a.supercommutator(b)
            -5*x*y + 8*x*z - 2*y*z - 6*x + 12*y - 5*z
            sage: a.supercommutator(Cl.one())
            0
            sage: Cl.one().supercommutator(a)
            0
            sage: Cl.zero().supercommutator(a)
            0
            sage: a.supercommutator(Cl.zero())
            0

            sage: Q = QuadraticForm(ZZ, 2, [-1,1,-3])
            sage: Cl.<x,y> = CliffordAlgebra(Q)
            sage: [a.supercommutator(b) for a in Cl.basis() for b in Cl.basis()]
            [0, 0, 0, 0, 0, -2, 1, -x - 2*y, 0, 1,
             -6, 6*x + y, 0, x + 2*y, -6*x - y, 0]
            sage: [a*b-b*a for a in Cl.basis() for b in Cl.basis()]
            [0, 0, 0, 0, 0, 0, 2*x*y - 1, -x - 2*y, 0,
             -2*x*y + 1, 0, 6*x + y, 0, x + 2*y, -6*x - y, 0]

        Exterior algebras inherit from Clifford algebras, so
        supercommutators work as well. We verify the exterior algebra
        is supercommutative::

            sage: E.<x,y,z,w> = ExteriorAlgebra(QQ)
            sage: all(b1.supercommutator(b2) == 0
            ....:     for b1 in E.basis() for b2 in E.basis())
            True
        """
        P = self.parent()
        ret = P.zero()
        for ms,cs in self:
            for mx,cx in x:
                ret += P.term(ms, cs) * P.term(mx, cx)
                s = (-1)**(P.degree_on_basis(ms) * P.degree_on_basis(mx))
                ret -= s * P.term(mx, cx) * P.term(ms, cs)
        return ret

class CliffordAlgebra(CombinatorialFreeModule):
    r"""
    The Clifford algebra of a quadratic form.

    Let `Q : V \to \mathbf{k}` denote a quadratic form on a vector space `V`
    over a field `\mathbf{k}`. The Clifford algebra `Cl(V, Q)` is defined as
    `T(V) / I_Q` where `T(V)` is the tensor algebra of `V` and `I_Q` is the
    two-sided ideal generated by all elements of the form `v \otimes v - Q(v)`
    for all `v \in V`.

    We abuse notation to denote the projection of a pure tensor
    `x_1 \otimes x_2 \otimes \cdots \otimes x_m \in T(V)` onto
    `T(V) / I_Q = Cl(V, Q)` by `x_1 \wedge x_2 \wedge \cdots \wedge x_m`.
    This is motivated by the fact that `Cl(V, Q)` is the exterior algebra
    `\wedge V` when `Q = 0` (one can also think of a Clifford algebra as
    a quantization of the exterior algebra). See :class:`ExteriorAlgebra`
    for the concept of an exterior algebra.

    From the definition, a basis of `Cl(V, Q)` is given by monomials of
    the form

    .. MATH::

        \{ e_{i_1} \wedge \cdots \wedge e_{i_k} \mid 1 \leq i_1 < \cdots <
        i_k \leq n \},

    where `n = \dim(V)` and where `\{ e_1, e_2, \cdots, e_n \}` is any
    fixed basis of `V`. Hence

    .. MATH::

        \dim(Cl(V, Q)) = \sum_{k=0}^n \binom{n}{k} = 2^n.

    .. NOTE::

        The algebra `Cl(V, Q)` is a `\ZZ / 2\ZZ`-graded algebra, but not
        (in general) `\ZZ`-graded (in a reasonable way).

    This construction satisfies the following universal property. Let
    `i : V \to Cl(V, Q)` denote the natural inclusion (which is an
    embedding). Then for every associative `\mathbf{k}`-algebra `A`
    and any `\mathbf{k}`-linear map `j : V \to A` satisfying

    .. MATH::

        j(v)^2 = Q(v) \cdot 1_A

    for all `v \in V`, there exists a unique `\mathbf{k}`-algebra
    homomorphism `f : Cl(V, Q) \to A` such that `f \circ i = j`.
    This property determines the Clifford algebra uniquely up to
    canonical isomorphism. The inclusion `i` is commonly used to
    identify `V` with a vector subspace of `Cl(V)`.

    The Clifford algebra also can be considered as a covariant functor
    from the category of vector spaces equipped with quadratic forms
    to the category of algebras. In fact, if `(V, Q)` and `(W, R)`
    are two vector spaces endowed with quadratic forms, and if
    `g : W \to V` is a linear map preserving the quadratic form,
    then we can define an algebra morphism
    `Cl(g) : Cl(W, R) \to Cl(V, Q)` by requiring that it send every
    `w \in W` to `g(w) \in V`. Since the quadratic form `R` on `W`
    is uniquely determined by the quadratic form `Q` on `V` (due to
    the assumption that `g` preserves the quadratic form), this fact
    can be rewritten as follows: If `(V, Q)` is a vector space with a
    quadratic form, and `W` is another vector space, and
    `\phi : W \to V` is any linear map, then we obtain an algebra
    morphism `Cl(\phi) : Cl(W, \phi(Q)) \to Cl(V, Q)` where
    `\phi(Q) = \phi^T \cdot Q \cdot \phi` (we consider `\phi` as a
    matrix) is the quadratic form `Q` pulled back to `W`. In fact, the
    map `\phi` preserves the quadratic form because of

    .. MATH::

        \phi(Q)(x) = x^T \cdot \phi^T \cdot Q \cdot \phi \cdot x
        = (\phi \cdot x)^T \cdot Q \cdot (\phi \cdot x) = Q(\phi(x)).

    Hence we have `\phi(w)^2 = Q(\phi(w)) = \phi(Q)(w)` for all `w \in W`.

    REFERENCES:

    - :wikipedia:`Clifford_algebra`

    INPUT:

    - ``Q`` -- a quadratic form
    - ``names`` -- (default: ``'e'``) the generator names

    EXAMPLES:

    To create a Clifford algebra, all one needs to do is specify a
    quadratic form::

        sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
        sage: Cl = CliffordAlgebra(Q)
        sage: Cl
        The Clifford algebra of the Quadratic form in 3 variables over Integer Ring with coefficients: 
        [ 1 2 3 ]
        [ * 4 5 ]
        [ * * 6 ]

    We can also explicitly name the generators. In this example, the
    Clifford algebra we construct is an exterior algebra (since we
    choose the quadratic form to be zero)::

        sage: Q = QuadraticForm(ZZ, 4, [0]*10)
        sage: Cl.<a,b,c,d> = CliffordAlgebra(Q)
        sage: a*d
        a*d
        sage: d*c*b*a + a + 4*b*c
        a*b*c*d + 4*b*c + a
    """
    @staticmethod
    def __classcall_private__(cls, Q, names=None):
        """
        Normalize arguments to ensure a unique representation.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl1.<e0,e1,e2> = CliffordAlgebra(Q)
            sage: Cl2 = CliffordAlgebra(Q)
            sage: Cl3 = CliffordAlgebra(Q, ['e0','e1','e2'])
            sage: Cl1 is Cl2 and Cl2 is Cl3
            True
        """
        if not isinstance(Q, QuadraticForm):
            raise ValueError("{} is not a quadratic form".format(Q))
        if names is None:
            names = 'e'
        names = tuple(names)
        if len(names) != Q.dim():
            if len(names) == 1:
                names = tuple( '{}{}'.format(names[0], i) for i in range(Q.dim()) )
            else:
                raise ValueError("the number of variables does not match the number of generators")
        return super(CliffordAlgebra, cls).__classcall__(cls, Q, names)

    def __init__(self, Q, names, category=None):
        r"""
        Initialize ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl = CliffordAlgebra(Q)
            sage: TestSuite(Cl).run()

        TESTS:

        We check that the basis elements are indeed indexed by
        *strictly increasing* tuples::

            sage: Q = QuadraticForm(ZZ, 9)
            sage: Cl = CliffordAlgebra(Q)
            sage: ba = Cl.basis().keys()
            sage: all( tuple(sorted(S)) in ba
            ....:      for S in Subsets(range(9)) )
            True
        """
        self._quadratic_form = Q
        R = Q.base_ring()
        if category is None:
            category = AlgebrasWithBasis(R).Super()
        indices = SubsetsSorted(range(Q.dim()))
        CombinatorialFreeModule.__init__(self, R, indices, category=category)
        self._assign_names(names)

    def _repr_(self):
        r"""
        Return a string representation of ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: CliffordAlgebra(Q)
            The Clifford algebra of the Quadratic form in 3 variables over Integer Ring with coefficients: 
            [ 1 2 3 ]
            [ * 4 5 ]
            [ * * 6 ]
        """
        return "The Clifford algebra of the {}".format(self._quadratic_form)

    def _repr_term(self, m):
        """
        Return a string representation of the basis element indexed by ``m``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl._repr_term((0,2))
            'x*z'
            sage: Cl._repr_term(())
            '1'
            sage: Cl._repr_term((1,))
            'y'
        """
        if not m:
            return '1'
        term = ''
        for i in m:
            if term:
                term += '*'
            term += self.variable_names()[i]
        return term

    def _latex_term(self, m):
        r"""
        Return a `\LaTeX` representation of the basis element indexed
        by ``m``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl._latex_term((0,2))
            ' x z'
        """
        if not m:
            return '1'
        term = ''
        for i in m:
            term += ' ' + self.latex_variable_names()[i]
        return term

    def _coerce_map_from_(self, V):
        """
        Return if there is a coerce map from ``V`` into ``self``.

        The things which coerce into ``self`` are:

        - Clifford algebras with the same generator names and an equal
          quadratic form over a ring which coerces into the base
          ring of ``self``.
        - The underlying free module of ``self``.
        - The base ring of ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Qp = QuadraticForm(QQ, 3, [1,2,3,4,5,6])
            sage: Cl = CliffordAlgebra(Q)
            sage: Clp = CliffordAlgebra(Qp)
            sage: Cl.has_coerce_map_from(Clp)
            False
            sage: Clp.has_coerce_map_from(Cl)
            True

        Check that we preserve the multiplicative structure::

            sage: all(Clp(b)*Clp(b) == Clp(b*b) for b in Cl.basis())
            True

        Check from the underlying free module::

            sage: M = ZZ^3
            sage: Mp = QQ^3
            sage: Cl.has_coerce_map_from(M)
            True
            sage: Cl.has_coerce_map_from(Mp)
            False
            sage: Clp.has_coerce_map_from(M)
            True
            sage: Clp.has_coerce_map_from(Mp)
            True

        Names matter::

            sage: Cln = CliffordAlgebra(Q, names=['x','y','z'])
            sage: Cln.has_coerce_map_from(Cl)
            False
            sage: Cl.has_coerce_map_from(Cln)
            False

        Non-injective homomorphisms of base rings don't cause zero
        values in the coordinate dictionary (this had to be manually
        ensured)::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Qp = QuadraticForm(Integers(3), 3, [1,2,3,4,5,6])
            sage: Cl = CliffordAlgebra(Q)
            sage: Clp = CliffordAlgebra(Qp)
            sage: a = Cl.basis()[(1,2)]
            sage: a
            e1*e2
            sage: Clp(a) # so far so good
            e1*e2
            sage: Clp(3*a) # but now
            0
            sage: Clp(3*a) == 0
            True
            sage: b = Cl.basis()[(0,2)]
            sage: Clp(3*a-4*b)
            2*e0*e2
        """
        if isinstance(V, CliffordAlgebra):
            Q = self._quadratic_form
            try:
                return (V.variable_names() == self.variable_names() and
                        V._quadratic_form.base_change_to(self.base_ring()) == Q)
            except Exception:
                return False

        if self.free_module().has_coerce_map_from(V):
            return True

        return super(CliffordAlgebra, self)._coerce_map_from_(V)

    def _element_constructor_(self, x):
        """
        Construct an element of ``self`` from ``x``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Qp = QuadraticForm(QQ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Clp = CliffordAlgebra(Qp, names=['x','y','z'])
            sage: M = ZZ^3
            sage: Mp = QQ^3
            sage: Cl(2/3)
            Traceback (most recent call last):
            ...
            TypeError: do not know how to make x (= 2/3) an element of self ... 
            sage: Clp(2/3)
            2/3
            sage: Clp(x)
            x
            sage: M = ZZ^3
            sage: Clp( M((1,-3,2)) )
            x - 3*y + 2*z

        Zero coordinates are handled appropriately::

            sage: Q3 = QuadraticForm(Integers(3), 3, [1,2,3,4,5,6])
            sage: Cl3 = CliffordAlgebra(Q3, names='xyz')  # different syntax for a change
            sage: Cl3( M((1,-3,2)) )
            x + 2*z
        """
        # This is the natural lift morphism of the underlying free module
        if x in self.free_module():
            R = self.base_ring()
            if x.parent().base_ring() is R:
                return self.element_class(self, {(i,): c for i,c in x.iteritems()})
            return self.element_class(self, {(i,): R(c) for i,c in x.iteritems() if R(c) != R.zero()})

        if isinstance(x, CliffordAlgebraElement):
            if x.parent() is self:
                return x
            if self.has_coerce_map_from(x.parent()):
                R = self.base_ring()
                return self.element_class(self, {i: R(c) for i,c in x if R(c) != R.zero()})

        return super(CliffordAlgebra, self)._element_constructor_(x)

    def gen(self, i):
        """
        Return the ``i``-th standard generator of the algebra ``self``.

        This is the ``i``-th basis vector of the vector space on which
        the quadratic form defining ``self`` is defined, regarded as an
        element of ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: [Cl.gen(i) for i in range(3)]
            [x, y, z]
        """
        return self._from_dict({(i,): self.base_ring().one()}, remove_zeros=False)

    def algebra_generators(self):
        """
        Return the algebra generators of ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.algebra_generators()
            Finite family {'y': y, 'x': x, 'z': z}
        """
        d = {x: self.gen(i) for i,x in enumerate(self.variable_names())}
        return Family(self.variable_names(), lambda x: d[x])

    def gens(self):
        r"""
        Return the generators of ``self`` (as an algebra).

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.gens()
            (x, y, z)
        """
        return tuple(self.algebra_generators())

    def ngens(self):
        """
        Return the number of algebra generators of ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.ngens()
            3
        """
        return self._quadratic_form.dim()

    @cached_method
    def one_basis(self):
        """
        Return the basis index of the element `1`.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.one_basis()
            ()
        """
        return ()

    def is_commutative(self):
        """
        Check if ``self`` is a commutative algebra.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.is_commutative()
            False
        """
        return self._quadratic_form.dim() < 2

    def quadratic_form(self):
        """
        Return the quadratic form of ``self``.

        This is the quadratic form used to define ``self``. The
        quadratic form on ``self`` is yet to be implemented.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.quadratic_form()
            Quadratic form in 3 variables over Integer Ring with coefficients: 
            [ 1 2 3 ]
            [ * 4 5 ]
            [ * * 6 ]
        """
        return self._quadratic_form

    def degree_on_basis(self, m):
        r"""
        Return the degree of the monomial indexed by ``m``.

        This degree is a nonnegative integer, and should be interpreted
        as a residue class modulo `2`, since we consider ``self`` to be
        `\ZZ_2`-graded (not `\ZZ`-graded, although there is a natural
        *filtration* by the length of ``m``). The degree of the monomial
        ``m`` in this `\ZZ_2`-grading is defined to be the length of ``m``
        taken mod `2`.

        .. WARNING:

            On the :class:`ExteriorAlgebra` class (which inherits from
            :class:`CliffordAlgebra`), the :meth:`degree_on_basis`
            method is overridden to return an actual `\NN`-degree. So
            don't count on this method always returning `0` or `1` !!

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.degree_on_basis((0,))
            1
            sage: Cl.degree_on_basis((0,1))
            0
        """
        return len(m) % ZZ(2)

    @cached_method
    def free_module(self):
        """
        Return the underlying free module `V` of ``self``.

        This is the free module on which the quadratic form that was
        used to construct ``self`` is defined.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.free_module()
            Ambient free module of rank 3 over the principal ideal domain Integer Ring
        """
        return FreeModule(self.base_ring(), self._quadratic_form.dim())

    def dimension(self):
        """
        Return the rank of ``self`` as a free module.

        Let `V` be a free `R`-module of rank `n`; then, `Cl(V, Q)` is a
        free `R`-module of rank `2^n`.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.dimension()
            8
        """
        return ZZ(2)**self._quadratic_form.dim()

    def pseudoscalar(self):
        """
        Return the unit pseudoscalar of ``self``.

        Given the basis `e_1, e_2, \ldots, e_n` of the underlying
        `R`-module, the unit pseudoscalar is defined as
        `e_1 \cdot e_2 \cdots e_n`.

        This depends on the choice of basis.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.pseudoscalar()
            x*y*z

            sage: Q = QuadraticForm(ZZ, 0, [])
            sage: Cl = CliffordAlgebra(Q)
            sage: Cl.pseudoscalar()
            1

        REFERENCES:

        - :wikipedia:`Classification_of_Clifford_algebras#Unit_pseudoscalar`
        """
        d = self._quadratic_form.dim()
        return self.element_class(self, {tuple(range(d)): self.base_ring().one()})

    def lift_module_morphism(self, m, names=None):
        r"""
        Lift the matrix ``m`` to an algebra morphism of Clifford algebras.

        Given a linear map `m : W \to V` (here represented by a matrix
        acting on column vectors), this method returns the algebra
        morphism `Cl(m) : Cl(W, m(Q)) \to Cl(V, Q)`, where `Cl(V, Q)`
        is the Clifford algebra ``self`` and where `m(Q)` is the pullback
        of the quadratic form `Q` to `W`. See the documentation
        of :class:`CliffordAlgebra` for how this pullback and the
        morphism `Cl(m)` are defined.

        .. NOTE::

            This is a map into ``self``.

        INPUT:

        - ``m`` -- a matrix
        - ``names`` -- (default: ``'e'``) the names of the generators of the
          Clifford algebra of the domain of (the map represented by) ``m``

        OUTPUT:

        The algebra morphism `Cl(m)` from `Cl(W, m(Q))` to ``self``.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: m = matrix([[1,-1,-1],[0,1,-1],[1,1,1]])
            sage: phi = Cl.lift_module_morphism(m, 'abc')
            sage: phi
            Generic morphism:
              From: The Clifford algebra of the Quadratic form in 3 variables over Integer Ring with coefficients:
            [ 10 17 3 ]
            [ * 11 0 ]
            [ * * 5 ]
              To:   The Clifford algebra of the Quadratic form in 3 variables over Integer Ring with coefficients:
            [ 1 2 3 ]
            [ * 4 5 ]
            [ * * 6 ]
            sage: a,b,c = phi.domain().gens()
            sage: phi(a)
            x + z
            sage: phi(b)
            -x + y + z
            sage: phi(c)
            -x - y + z
            sage: phi(a + 3*b)
            -2*x + 3*y + 4*z
            sage: phi(a) + 3*phi(b)
            -2*x + 3*y + 4*z
            sage: phi(a*b)
            x*y + 2*x*z - y*z + 7
            sage: phi(b*a)
            -x*y - 2*x*z + y*z + 10
            sage: phi(a*b + c)
            x*y + 2*x*z - y*z - x - y + z + 7
            sage: phi(a*b) + phi(c)
            x*y + 2*x*z - y*z - x - y + z + 7

        We check that the map is an algebra morphism::

            sage: phi(a)*phi(b)
            x*y + 2*x*z - y*z + 7
            sage: phi(a*b)
            x*y + 2*x*z - y*z + 7
            sage: phi(a*a)
            10
            sage: phi(a)*phi(a)
            10
            sage: phi(b*a)
            -x*y - 2*x*z + y*z + 10
            sage: phi(b) * phi(a)
            -x*y - 2*x*z + y*z + 10
            sage: phi((a + b)*(a + c)) == phi(a + b) * phi(a + c)
            True

        We can also lift arbitrary linear maps::

            sage: m = matrix([[1,1],[0,1],[1,1]])
            sage: phi = Cl.lift_module_morphism(m, 'ab')
            sage: a,b = phi.domain().gens()
            sage: phi(a)
            x + z
            sage: phi(b)
            x + y + z
            sage: phi(a*b)
            x*y - y*z + 15
            sage: phi(a)*phi(b)
            x*y - y*z + 15
            sage: phi(b*a)
            -x*y + y*z + 12
            sage: phi(b)*phi(a)
            -x*y + y*z + 12

            sage: m = matrix([[1,1,1,2], [0,1,1,1], [0,1,1,1]])
            sage: phi = Cl.lift_module_morphism(m, 'abcd')
            sage: a,b,c,d = phi.domain().gens()
            sage: phi(a)
            x
            sage: phi(b)
            x + y + z
            sage: phi(c)
            x + y + z
            sage: phi(d)
            2*x + y + z
            sage: phi(a*b*c + d*a)
            -x*y - x*z + 21*x + 7
            sage: phi(a*b*c*d)
            21*x*y + 21*x*z + 42
        """
        Q = self._quadratic_form(m)
        # If R is a quadratic form and m is a matrix, then R(m) returns
        # the quadratic form m^t R m.

        if Q == self._quadratic_form and names is None:
            Cl = self
        else:
            Cl = CliffordAlgebra(Q, names)

        n = self._quadratic_form.dim()
        f = lambda x: self.prod(self._from_dict( {(j,): m[j,i] for j in range(n)},
                                                 remove_zeros=True )
                                for i in x)
        return Cl.module_morphism(on_basis=f, codomain=self,
                                  category=AlgebrasWithBasis(self.base_ring()).Graded())

    def lift_isometry(self, m, names=None):
        r"""
        Lift an invertible isometry ``m`` of the quadratric form of
        ``self`` to a Clifford algebra morphism.

        Given an invertible linear map `m : V \to W` (here represented by
        a matrix acting on column vectors), this method returns the
        algebra morphism `Cl(m)` from `Cl(V, Q)` to `Cl(W, m^{-1}(Q))`,
        where `Cl(V, Q)` is the Clifford algebra ``self`` and where
        `m^{-1}(Q)` is the pullback of the quadratic form `Q` to `W` along
        the inverse map `m^{-1} : W \to V`. See the documentation of
        :class:`CliffordAlgebra` for how this pullback and the morphism
        `Cl(m)` are defined.

        INPUT:

        - ``m`` -- an isometry of the quadratic form of ``self``
        - ``names`` -- (default: ``'e'``) the names of the generators of
          the Clifford algebra of the codomain of (the map represented by)
          ``m``

        OUTPUT:

        The algebra morphism `Cl(m)` from ``self`` to `Cl(W, m^{-1}(Q))`.

        EXAMPLES::

            sage: Q = QuadraticForm(ZZ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: m = matrix([[1,1,2],[0,1,1],[0,0,1]])
            sage: phi = Cl.lift_isometry(m, 'abc')
            sage: phi(x)
            a
            sage: phi(y)
            a + b
            sage: phi(x*y)
            a*b + 1
            sage: phi(x) * phi(y)
            a*b + 1
            sage: phi(z*y)
            a*b - a*c - b*c
            sage: phi(z) * phi(y)
            a*b - a*c - b*c
            sage: phi(x + z) * phi(y + z) == phi((x + z) * (y + z))
            True
        """
        MS = m.parent()
        if not m.is_invertible():
            raise ValueError('{} is not invertible')
        Q = self._quadratic_form(MS(m.inverse()))

        if Q == self._quadratic_form and names is None:
            Cl = self
        else:
            if names is None:
                names = 'e'
            Cl = CliffordAlgebra(Q, names)

        n = Q.dim()
        f = lambda x: Cl.prod(Cl._from_dict( {(j,): m[j,i] for j in range(n)},
                                             remove_zeros=True )
                              for i in x)
        return self.module_morphism(on_basis=f, codomain=Cl,
                                    category=AlgebrasWithBasis(self.base_ring()).Super())

    # This is a general method for finite dimensional algebras with bases
    #   and should be moved to the corresponding category once there is
    #   a category level method for getting the indexing set of the basis;
    #   similar to #15289 but on a category level.
    @cached_method
    def center_basis(self):
        """
        Return a list of elements which correspond to a basis for the center
        of ``self``.

        This assumes that the ground ring can be used to compute the
        kernel of a matrix.

        .. SEEALSO::

            :meth:`supercenter_basis`,
            http://math.stackexchange.com/questions/129183/center-of-clifford-algebra-depending-on-the-parity-of-dim-v

        .. TODO::

            Deprecate this in favor of a method called `center()` once
            subalgebras are properly implemented in Sage.

        EXAMPLES::

            sage: Q = QuadraticForm(QQ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Z = Cl.center_basis(); Z
            (1, -2/5*x*y*z + x - 3/5*y + 2/5*z)
            sage: all(z*b - b*z == 0 for z in Z for b in Cl.basis())
            True

            sage: Q = QuadraticForm(QQ, 3, [1,-2,-3, 4, 2, 1])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Z = Cl.center_basis(); Z
            (1, -x*y*z + x + 3/2*y - z)
            sage: all(z*b - b*z == 0 for z in Z for b in Cl.basis())
            True

            sage: Q = QuadraticForm(QQ, 2, [1,-2,-3])
            sage: Cl.<x,y> = CliffordAlgebra(Q)
            sage: Cl.center_basis()
            (1,)

            sage: Q = QuadraticForm(QQ, 2, [-1,1,-3])
            sage: Cl.<x,y> = CliffordAlgebra(Q)
            sage: Cl.center_basis()
            (1,)

        A degenerate case::

            sage: Q = QuadraticForm(QQ, 3, [4,4,-4,1,-2,1])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.center_basis()
            (1, x*y*z + x - 2*y - 2*z, x*y + x*z - 2*y*z)

        The most degenerate case (the exterior algebra)::

            sage: Q = QuadraticForm(QQ, 3)
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.center_basis()
            (1, x*y, x*z, y*z, x*y*z)
        """
        R = self.base_ring()
        B = self.basis()
        K = list(B.keys())
        k = len(K)
        d = {}
        for a,i in enumerate(K):
            Bi = B[i]
            for b,j in enumerate(K):
                Bj = B[j]
                for m,c in (Bi*Bj - Bj*Bi):
                    d[(a, K.index(m)+k*b)] = c
        m = Matrix(R, d, nrows=k, ncols=k*k, sparse=True)
        from_vector = lambda x: self.sum_of_terms(((K[i], c) for i,c in x.iteritems()),
                                                  distinct=True)
        return tuple(map( from_vector, m.kernel().basis() ))

        # Dense version
        # R = self.base_ring()
        # B = self.basis()
        # K = list(B.keys())
        # eqns = [[] for dummy in range(k)]
        # for a,i in enumerate(K):
        #     for b,j in enumerate(K):
        #         v = B[i]*B[j] - B[j]*B[i]
        #         eqns[a].extend([v[k] for k in K])
        # m = Matrix(R, eqns)
        # from_vector = lambda x: self.sum_of_terms(((K[i], c) for i,c in x.iteritems()),
        #                                           distinct=True)
        # return tuple(map( from_vector, m.kernel().basis() ))

    # Same as center except for superalgebras
    @cached_method
    def supercenter_basis(self):
        """
        Return a list of elements which correspond to a basis for the
        supercenter of ``self``.

        This assumes that the ground ring can be used to compute the
        kernel of a matrix.

        .. SEEALSO::

            :meth:`center_basis`,
            http://math.stackexchange.com/questions/129183/center-of-clifford-algebra-depending-on-the-parity-of-dim-v

        .. TODO::

            Deprecate this in favor of a method called `supercenter()` once
            subalgebras are properly implemented in Sage.

        EXAMPLES::

            sage: Q = QuadraticForm(QQ, 3, [1,2,3,4,5,6])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: SZ = Cl.supercenter_basis(); SZ
            (1,)
            sage: all(z.supercommutator(b) == 0 for z in SZ for b in Cl.basis())
            True

            sage: Q = QuadraticForm(QQ, 3, [1,-2,-3, 4, 2, 1])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.supercenter_basis()
            (1,)

            sage: Q = QuadraticForm(QQ, 2, [1,-2,-3])
            sage: Cl.<x,y> = CliffordAlgebra(Q)
            sage: Cl.supercenter_basis()
            (1,)

            sage: Q = QuadraticForm(QQ, 2, [-1,1,-3])
            sage: Cl.<x,y> = CliffordAlgebra(Q)
            sage: Cl.supercenter_basis()
            (1,)

        Singular vectors of a quadratic form generate in the supercenter::

            sage: Q = QuadraticForm(QQ, 3, [1/2,-2,4,256/249,3,-185/8])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.supercenter_basis()
            (1, x + 249/322*y + 22/161*z)

            sage: Q = QuadraticForm(QQ, 3, [4,4,-4,1,-2,1])
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.supercenter_basis()
            (1, x + 2*z, y + z, x*y + x*z - 2*y*z)

        The most degenerate case::

            sage: Q = QuadraticForm(QQ, 3)
            sage: Cl.<x,y,z> = CliffordAlgebra(Q)
            sage: Cl.supercenter_basis()
            (1, x, y, z, x*y, x*z, y*z, x*y*z)
        """
        R = self.base_ring()
        B = self.basis()
        K = list(B.keys())
        k = len(K)
        d = {}
        for a,i in enumerate(K):
            Bi = B[i]
            for b,j in enumerate(K):
                Bj = B[j]
                if len(i) % 2 and len(j) % 2:
                    supercommutator = Bi * Bj + Bj * Bi
                else:
                    supercommutator = Bi * Bj - Bj * Bi
                for m,c in supercommutator:
                    d[(a, K.index(m)+k*b)] = c
        m = Matrix(R, d, nrows=k, ncols=k*k, sparse=True)
        from_vector = lambda x: self.sum_of_terms(((K[i], c) for i,c in x.iteritems()),
                                                  distinct=True)
        return tuple(map( from_vector, m.kernel().basis() ))

        # Dense version
        # R = self.base_ring()
        # B = self.basis()
        # K = list(B.keys())
        # eqns = [[] for dummy in range(k)]
        # for a,i in enumerate(K):
        #     for b,j in enumerate(K):
        #         v = B[i].supercommutator(B[j])   # or better an if-loop as above
        #         eqns[a].extend([v[k] for k in K])
        # m = Matrix(R, eqns)
        # from_vector = lambda x: self.sum_of_terms(((K[i], c) for i,c in x.iteritems()),
        #                                           distinct=True)
        # return tuple(map( from_vector, m.kernel().basis() ))

    Element = CliffordAlgebraElement

class ExteriorAlgebra(CliffordAlgebra):
    r"""
    An exterior algebra of a free module over a commutative ring.

    Let `V` be a module over a commutative ring `R`. The exterior algebra
    (or Grassmann algebra) `\Lambda(V)` of `V` is defined as the quotient
    of the tensor algebra `T(V)` of `V` modulo the two-sided ideal
    generated by all tensors of the form `x \otimes x` with `x \in V`. The
    multiplication on `\Lambda(V)` is denoted by `\wedge` (so
    `v_1 \wedge v_2 \wedge \cdots \wedge v_n` is the projection of
    `v_1 \otimes v_2 \otimes \cdots \otimes v_n` onto `\Lambda(V)`) and
    called the "exterior product" or "wedge product".

    If `V` is a rank-`n` free `R`-module with a basis
    `\{e_1, \ldots, e_n\}`, then `\Lambda(V)` is the `R`-algebra
    noncommutatively generated by the `n` generators `e_1, \ldots, e_n`
    subject to the relations `e_i^2 = 0` for all `i`, and
    `e_i e_j = - e_j e_i` for all `i < j`. As an `R`-module,
    `\Lambda(V)` then has a basis `(\bigwedge_{i \in I} e_i)` with `I`
    ranging over the subsets of `\{1, 2, \ldots, n\}` (where
    `\bigwedge_{i \in I} e_i` is the wedge product of `e_i` for `i`
    running through all elements of `I` from smallest to largest), and
    hence is free of rank `2^n`.

    The exterior algebra of an `R`-module `V` can also be realized
    as the Clifford algebra of `V` for the quadratic form `Q` given by
    `Q(v) = 0` for all vectors `v \in V`. See :class:`CliffordAlgebra`
    for the notion of a Clifford algebra.

    The exterior algebra of an `R`-module `V` is a `\ZZ`-graded connected
    Hopf superalgebra. It is commutative in the super sense (i.e., the
    odd elements anticommute and square to `0`).

    This class implements the exterior algebra `\Lambda(R^n)` for
    `n` a nonnegative integer.

    .. WARNING::

        We initialize the exterior algebra as an object of the category
        of Hopf algebras, but this is not really correct, since it is a
        Hopf superalgebra with the odd-degree components forming the odd
        part. So use Hopf-algebraic methods with care!

    .. TODO::

        Add a category for Hopf superalgebras (perhaps part of :trac:`16513`).

    INPUT:

    - ``R`` -- the base ring, *or* the free module whose exterior algebra
      is to be computed

    - ``names`` -- a list of strings to name the generators of the
      exterior algebra; this list can either have one entry only (in which
      case the generators will be called ``e + '0'``, ``e + '1'``, ...,
      ``e + 'n-1'``, with ``e`` being said entry), or have ``n`` entries
      (in which case these entries will be used directly as names for the
      generators)

    - ``n`` -- the number of generators, i.e., the rank of the free
      module whose exterior algebra is to be computed (this doesn't have
      to be provided if it can be inferred from the rest of the input)

    REFERENCES:

    - :wikipedia:`Exterior_algebra`
    """
    @staticmethod
    def __classcall_private__(cls, R, names=None, n=None):
        """
        Normalize arguments to ensure a unique representation.

        EXAMPLES::

            sage: E1.<e0,e1,e2> = ExteriorAlgebra(QQ)
            sage: E2 = ExteriorAlgebra(QQ, 3)
            sage: E3 = ExteriorAlgebra(QQ, ['e0','e1','e2'])
            sage: E1 is E2 and E2 is E3
            True
        """
        if names is None:
            names = 'e'
        elif names in ZZ:
            n = names
            names = 'e'

        if isinstance(R, FreeModule_generic):
            if n is not None and n != R.dimension():
                raise ValueError("the number of variables does not match the dimension")
            n = R.dimension()
            R = R.base_ring()

        names = tuple(names)
        if n is not None and len(names) != n:
            if len(names) == 1:
                names = tuple( '{}{}'.format(names[0], i) for i in range(n) )
            else:
                raise ValueError("the number of variables does not match the number of generators")
        return super(ExteriorAlgebra, cls).__classcall__(cls, R, names)

    def __init__(self, R, names):
        """
        Initialize ``self``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: TestSuite(E).run()
        """
        CliffordAlgebra.__init__(self, QuadraticForm(R, len(names)), names, HopfAlgebrasWithBasis(R).Super())
        # TestSuite will fail if the HopfAlgebra classes will ever have tests for
        # the coproduct being an algebra morphism -- since this is really a
        # Hopf superalgebra, not a Hopf algebra.

    def _repr_(self):
        r"""
        Return a string representation of ``self``.

        EXAMPLES::

            sage: ExteriorAlgebra(QQ, 3)
            The exterior algebra of rank 3 over Rational Field
        """
        return "The exterior algebra of rank {} over {}".format(self.ngens(), self.base_ring())

    def _repr_term(self, m):
        """
        Return a string representation of the basis element indexed by
        ``m``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E._repr_term((0,1,2))
            'x^y^z'
        """
        if len(m) == 0:
            return '1'
        term = ''
        for i in m:
            if len(term) != 0:
                term += '^'
            term += self.variable_names()[i]
        return term

    def _latex_term(self, m):
        r"""
        Return a `\LaTeX` representation of the basis element indexed
        by ``m``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E._latex_term((0,1,2))
            ' x \\wedge y \\wedge z'
            sage: E.<x0,x1,x2> = ExteriorAlgebra(QQ)
            sage: E._latex_term((0,1,2))
            ' x_{0} \\wedge x_{1} \\wedge x_{2}'
            sage: E._latex_term(())
            '1'
            sage: E._latex_term((0,))
            ' x_{0}'
        """
        if len(m) == 0:
            return '1'
        term = ''
        for i in m:
            if len(term) != 0:
                term += ' \\wedge'
            term += ' ' + self.latex_variable_names()[i]
        return term

    def lift_morphism(self, phi, names=None):
        r"""
        Lift the matrix ``m`` to an algebra morphism of exterior algebras.

        Given a linear map `\phi : V \to W` (here represented by a matrix
        acting on column vectors over the base ring of `V`), this method
        returns the algebra morphism
        `\Lambda(\phi) : \Lambda(V) \to \Lambda(W)`. This morphism is defined
        on generators `v_i \in \Lambda(V)` by `v_i \mapsto \phi(v_i)`.

        .. NOTE::

            This is the map going out of ``self`` as opposed to
            :meth:`~sage.algebras.clifford_algebra.CliffordAlgebraElement.lift_module_morphism()`
            for general Clifford algebras.

        INPUT:

        - ``phi`` -- a linear map `\phi` from `V` to `W`, encoded as a
          matrix
        - ``names`` -- (default: ``'e'``) the names of the generators of
          the Clifford algebra of the domain of (the map represented by)
          ``phi``

        OUTPUT:

        The algebra morphism `\Lambda(\phi)` from ``self`` to `\Lambda(W)`.

        EXAMPLES::

            sage: E.<x,y> = ExteriorAlgebra(QQ)
            sage: phi = matrix([[0,1],[1,1],[1,2]]); phi
            [0 1]
            [1 1]
            [1 2]
            sage: L = E.lift_morphism(phi, ['a','b','c']); L
            Generic morphism:
              From: The exterior algebra of rank 2 over Rational Field
              To:   The exterior algebra of rank 3 over Rational Field
            sage: L(x)
            b + c
            sage: L(y)
            a + b + 2*c
            sage: L.on_basis()((1,))
            a + b + 2*c
            sage: p = L(E.one()); p
            1
            sage: p.parent()
            The exterior algebra of rank 3 over Rational Field
            sage: L(x*y)
            -a^b - a^c + b^c
            sage: L(x)*L(y)
            -a^b - a^c + b^c
            sage: L(x + y)
            a + 2*b + 3*c
            sage: L(x) + L(y)
            a + 2*b + 3*c
            sage: L(1/2*x + 2)
            1/2*b + 1/2*c + 2
            sage: L(E(3))
            3

            sage: psi = matrix([[1, -3/2]]); psi
            [   1 -3/2]
            sage: Lp = E.lift_morphism(psi, ['a']); Lp
            Generic morphism:
              From: The exterior algebra of rank 2 over Rational Field
              To:   The exterior algebra of rank 1 over Rational Field
            sage: Lp(x)
            a
            sage: Lp(y)
            -3/2*a
            sage: Lp(x + 2*y + 3)
            -2*a + 3
        """
        n = phi.nrows()
        R = self.base_ring()
        E = ExteriorAlgebra(R, names, n)
        f = lambda x: E.prod(E._from_dict( {(j,): phi[j,i] for j in range(n)},
                                           remove_zeros=True )
                             for i in x)
        return self.module_morphism(on_basis=f, codomain=E, category=AlgebrasWithBasis(R).Super())

    def volume_form(self):
        """
        Return the volume form of ``self``.

        Given the basis `e_1, e_2, \ldots, e_n` of the underlying
        `R`-module, the volume form is defined as `e_1 \wedge e_2
        \wedge \cdots \wedge e_n`.

        This depends on the choice of basis.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E.volume_form()
            x^y^z
        """
        d = self._quadratic_form.dim()
        return self.element_class(self, {tuple(range(d)): self.base_ring().one()})

    def boundary(self, s_coeff):
        r"""
        Return the boundary operator `\partial` defined by the structure
        coefficients ``s_coeff`` of a Lie algebra.

        For more on the boundary operator, see
        :class:`ExteriorAlgebraBoundary`.

        INPUT:

        - ``s_coeff`` -- a dictionary whose keys are in `I \times I`, where
          `I` is the index set of the underlying vector space `V`, and whose
          values can be coerced into 1-forms (degree 1 elements) in ``E``
          (usually, these values will just be elements of `V`)

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E.boundary({(0,1): z, (1,2): x, (2,0): y})
            Boundary endomorphism of The exterior algebra of rank 3 over Rational Field
        """
        return ExteriorAlgebraBoundary(self, s_coeff)

    def coboundary(self, s_coeff):
        r"""
        Return the coboundary operator `d` defined by the structure
        coefficients ``s_coeff`` of a Lie algebra.

        For more on the coboundary operator, see
        :class:`ExteriorAlgebraCoboundary`.

        INPUT:

        - ``s_coeff`` -- a dictionary whose keys are in `I \times I`, where
          `I` is the index set of the underlying vector space `V`, and whose
          values can be coerced into 1-forms (degree 1 elements) in ``E``
          (usually, these values will just be elements of `V`)

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E.coboundary({(0,1): z, (1,2): x, (2,0): y})
            Coboundary endomorphism of The exterior algebra of rank 3 over Rational Field
        """
        return ExteriorAlgebraCoboundary(self, s_coeff)

    def degree_on_basis(self, m):
        r"""
        Return the degree of the monomial indexed by ``m``.

        The degree of ``m`` in the `\ZZ`-grading of ``self`` is defined
        to be the length of ``m``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E.degree_on_basis(())
            0
            sage: E.degree_on_basis((0,))
            1
            sage: E.degree_on_basis((0,1))
            2
        """
        return ZZ(len(m))

    def coproduct_on_basis(self, a):
        r"""
        Return the coproduct on the basis element indexed by ``a``.

        The coproduct is defined by

        .. MATH::

            \Delta(e_{i_1} \wedge \cdots \wedge e_{i_m}) = \sum_{k=0}^m
            \sum_{\sigma \in Ush_{k,m-k}} (-1)^{\sigma}
            (e_{i_{\sigma(1)}} \wedge \cdots \wedge e_{i_{\sigma(k)}}) \otimes
            (e_{i_{\sigma(k+1)}} \wedge \cdots \wedge e_{i_{\sigma(m)}}),

        where `Ush_{k,m-k}` denotes the set of all `(k,m-k)`-unshuffles
        (i.e., permutations in `S_m` which are increasing on the interval
        `\{1, 2, \ldots, k\}` and on the interval
        `\{k+1, k+2, \ldots, k+m\}`).

        .. WARNING::

            This coproduct is a homomorphism of superalgebras, not a
            homomorphism of algebras!

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E.coproduct_on_basis((0,))
            1 # x + x # 1
            sage: E.coproduct_on_basis((0,1))
            1 # x^y + x # y + x^y # 1 - y # x
            sage: E.coproduct_on_basis((0,1,2))
            1 # x^y^z + x # y^z + x^y # z + x^y^z # 1
             - x^z # y - y # x^z + y^z # x + z # x^y
        """
        from sage.combinat.combinat import unshuffle_iterator
        one = self.base_ring().one()
        return self.tensor_square().sum_of_terms(unshuffle_iterator(a, one),
                                                 distinct=True)

    def antipode_on_basis(self, m):
        r"""
        Return the antipode on the basis element indexed by ``m``.

        Given a basis element `\omega`, the antipode is defined by
        `S(\omega) = (-1)^{\deg(\omega)} \omega`.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E.antipode_on_basis(())
            1
            sage: E.antipode_on_basis((1,))
            -y
            sage: E.antipode_on_basis((1,2))
            y^z
        """
        return self.term(m, (-self.base_ring().one())**len(m))

    def counit(self, x):
        """
        Return the counit of ``x``.

        The counit of an element `\omega` of the exterior algebra
        is its constant coefficient.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: elt = x*y - 2*x + 3
            sage: E.counit(elt)
            3
        """
        return x.constant_coefficient()

    def interior_product_on_basis(self, a, b):
        """
        Return the interior product `\iota_b a` of ``a`` with respect to
        ``b``.

        See :meth:`~sage.algebras.clifford_algebra.CliffordAlgebra.Element.interior_product`
        for more information.

        In this method, ``a`` and ``b`` are supposed to be
        basis elements (see
        :meth:`~sage.algebras.clifford_algebra.CliffordAlgebra.Element.interior_product`
        for a method that computes interior product of arbitrary
        elements), and to be input as their keys.

        This depends on the choice of basis of the vector space
        whose exterior algebra is ``self``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: E.interior_product_on_basis((0,), (0,))
            1
            sage: E.interior_product_on_basis((0,2), (0,))
            z
            sage: E.interior_product_on_basis((1,), (0,2))
            0
            sage: E.interior_product_on_basis((0,2), (1,))
            0
            sage: E.interior_product_on_basis((0,1,2), (0,2))
            -y
        """
        sgn = True
        t = list(a)
        for i in b:
            if i not in t:
                return self.zero()
            if t.index(i) % 2:
                sgn = not sgn
            t.remove(i)
        R = self.base_ring()
        return self.term(tuple(t), (R.one() if sgn else - R.one()))

    def lifted_bilinear_form(self, M):
        r"""
        Return the bilinear form on the exterior algebra ``self``
        `= \Lambda(V)` which is obtained by lifting the bilinear
        form `f` on `V` given by the matrix ``M``.

        Let `V` be a module over a commutative ring `R`, and let
        `f : V \times V \to R` be a bilinear form on `V`. Then,
        a bilinear form `\Lambda(f) : \Lambda(V) \times
        \Lambda(V) \to R` on `\Lambda(V)` can be canonically
        defined as follows: For every `n \in \NN`, `m \in \NN`,
        `v_1, v_2, \ldots, v_n, w_1, w_2, \ldots, w_m \in V`,
        we define

        .. MATH::

            \Lambda(f)
            ( v_1 \wedge v_2 \wedge \cdots \wedge v_n ,
              w_1 \wedge w_2 \wedge \cdots \wedge w_m )
            := \begin{cases}
              0, &\mbox{if } n \neq m ; \\
              \det G, & \mbox{if } n = m \end{cases} ,

        where `G` is the `n \times m`-matrix whose
        `(i, j)`-th entry is `f(v_i, w_j)`. This bilinear form
        `\Lambda(f)` is known as the bilinear form on
        `\Lambda(V)` obtained by lifting the bilinear form `f`.
        Its restriction to the `1`-st homogeneous component
        `V` of `\Lambda(V)` is `f`.

        The bilinear form `\Lambda(f)` is symmetric if `f` is.

        INPUT:

        - ``M`` -- a matrix over the same base ring as ``self``,
          whose `(i, j)`-th entry is `f(e_i, e_j)`, where
          `(e_1, e_2, \ldots, e_N)` is the standard basis of the
          module `V` for which ``self`` `= \Lambda(V)` (so that
          `N = \dim(V)`), and where `f` is the bilinear form
          which is to be lifted.

        OUTPUT:

        A bivariate function which takes two elements `p` and
        `q` of ``self`` to `\Lambda(f)(p, q)`.

        .. NOTE::

            This takes a bilinear form on `V` as matrix, and
            returns a bilinear form on ``self`` as a function in
            two arguments. We do not return the bilinear form as
            a matrix since this matrix can be huge and one often
            needs just a particular value.

        .. TODO::

            Implement a class for bilinear forms and rewrite this
            method to use that class.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: M = Matrix(QQ, [[1, 2, 3], [2, 3, 4], [3, 4, 5]])
            sage: Eform = E.lifted_bilinear_form(M)
            sage: Eform
            Bilinear Form from Cartesian product of The exterior algebra of rank 3 over
             Rational Field, The exterior algebra of rank 3 over Rational Field to
             Rational Field
            sage: Eform(x*y, y*z)
            -1
            sage: Eform(x*y, y)
            0
            sage: Eform(x*(y+z), y*z)
            -3
            sage: Eform(x*(y+z), y*(z+x))
            0
            sage: N = Matrix(QQ, [[3, 1, 7], [2, 0, 4], [-1, -3, -1]])
            sage: N.determinant()
            -8
            sage: Eform = E.lifted_bilinear_form(N)
            sage: Eform(x, E.one())
            0
            sage: Eform(x, x*z*y)
            0
            sage: Eform(E.one(), E.one())
            1
            sage: Eform(E.zero(), E.one())
            0
            sage: Eform(x, y)
            1
            sage: Eform(z, y)
            -3
            sage: Eform(x*z, y*z)
            20
            sage: Eform(x+x*y+x*y*z, z+z*y+z*y*x)
            11

        TESTS:

        Exterior algebra over a zero space (a border case)::

            sage: E = ExteriorAlgebra(QQ, 0)
            sage: M = Matrix(QQ, [])
            sage: Eform = E.lifted_bilinear_form(M)
            sage: Eform(E.one(), E.one())
            1
            sage: Eform(E.zero(), E.one())
            0

        .. TODO::

            Another way to compute this bilinear form seems to be to
            map `x` and `y` to the appropriate Clifford algebra and
            there compute `x^t y`, then send the result back to the
            exterior algebra and return its constant coefficient. Or
            something like this. Once the maps to the Clifford and
            back are implemented, check if this is faster.
        """
        R = self.base_ring()
        def lifted_form(x, y):
            result = R.zero()
            for mx, cx in x:
                for my, cy in y:
                    n = len(mx)
                    m = len(my)
                    if m != n:
                        continue
                    MS = MatrixSpace(R, n, n)
                    MC = MS._get_matrix_class()
                    matrix_list = [M[mx[i], my[j]]
                                   for i in range(n)
                                   for j in range(n)]
                    matr = MC(MS, matrix_list, copy=False, coerce=False)
                    # Using low-level matrix constructor here
                    # because Matrix(...) does too much duck
                    # typing (:trac:`17124`).
                    result += cx * cy * matr.determinant()
            return result
        from sage.combinat.cartesian_product import CartesianProduct
        return PoorManMap(lifted_form, domain=CartesianProduct(self, self),
                          codomain=self.base_ring(),
                          name="Bilinear Form")

    class Element(CliffordAlgebraElement):
        """
        An element of an exterior algebra.
        """
        def _mul_(self, other):
            """
            Return ``self`` multiplied by ``other``.

            INPUT:

            - ``other`` -- element of the same exterior algebra as ``self``

            EXAMPLES::

                sage: E.<x,y,z> = ExteriorAlgebra(QQ)
                sage: x*y
                x^y
                sage: y*x
                -x^y
                sage: z*y*x
                -x^y^z
                sage: (x*z)*y
                -x^y^z
                sage: (3*x + y)^2
                0
                sage: (x - 3*y + z/3)^2
                0
                sage: (x+y) * (y+z)
                x^y + x^z + y^z
            """
            zero = self.parent().base_ring().zero()
            d = {}

            for ml,cl in self:
                for mr,cr in other:
                    # Create the next term
                    t = list(mr)
                    for i in reversed(ml):
                        pos = 0
                        for j in t:
                            if i == j:
                                pos = None
                                break
                            if i < j:
                                break
                            pos += 1
                            cr = -cr
                        if pos is None:
                            t = None
                            break
                        t.insert(pos, i)

                    if t is None: # The next term is 0, move along
                        continue

                    t = tuple(t)
                    d[t] = d.get(t, zero) + cl * cr
                    if d[t] == zero:
                        del d[t]

            return self.__class__(self.parent(), d)

        def interior_product(self, x):
            r"""
            Return the interior product (also known as antiderivation) of
            ``self`` with respect to ``x`` (that is, the element
            `\iota_{x}(\text{self})` of the exterior algebra).

            If `V` is an `R`-module, and if `\alpha` is a fixed element of
            `V^*`, then the *interior product* with respect to `\alpha` is
            an `R`-linear map
            `i_{\alpha} \colon \Lambda(V) \to \Lambda(V)`, determined by
            the following requirements:

            - `i_{\alpha}(v) = \alpha(v)` for all `v \in V = \Lambda^1(V)`,
            - it is a graded derivation of degree `-1`: all `x` and `y`
              in `\Lambda(V)` satisfy

            .. MATH::

                i_{\alpha}(x \wedge y) = (i_{\alpha} x) \wedge y
                + (-1)^{\deg x} x \wedge (i_{\alpha} y).

            It can be shown that this map `i_{\alpha}` is graded of
            degree `-1` (that is, sends `\Lambda^k(V)` into
            `\Lambda^{k-1}(V)` for every `k`).

            When `V` is a finite free `R`-module, the interior product can
            also be defined by

            .. MATH::

                (i_{\alpha} \omega)(u_1, \ldots, u_k)
                = \omega(\alpha, u_1, \ldots, u_k),

            where `\omega \in \Lambda^k(V)` is thought of as an
            alternating multilinear mapping from
            `V^* \times \cdots \times V^*` to `R`.

            Since Sage is only dealing with exterior powers of modules
            of the form `R^d` for some nonnegative integer `d`, the
            element `\alpha \in V^*` can be thought of as an element of
            `V` (by identifying the standard basis of `V = R^d` with its
            dual basis). This is how `\alpha` should be passed to this
            method.

            We then extend the interior product to all
            `\alpha \in \Lambda (V^*)` by

            .. MATH::

                i_{\beta \wedge \gamma} = i_{\gamma} \circ i_{\beta}.

            INPUT:

            - ``x`` -- element of (or coercing into) `\Lambda^1(V)`
              (for example, an element of `V`); this plays the role of
              `\alpha` in the above definition

            EXAMPLES::

                sage: E.<x,y,z> = ExteriorAlgebra(QQ)
                sage: x.interior_product(x)
                1
                sage: (x + x*y).interior_product(2*y)
                -2*x
                sage: (x*z + x*y*z).interior_product(2*y - x)
                -2*x^z - y^z - z
                sage: x.interior_product(E.one())
                x
                sage: E.one().interior_product(x)
                0
                sage: x.interior_product(E.zero())
                0
                sage: E.zero().interior_product(x)
                0

            REFERENCES:

            - :wikipedia:`Exterior_algebra#Interior_product`
            """
            P = self.parent()
            return P.sum([c * cx * P.interior_product_on_basis(m, mx)
                          for m,c in self for mx,cx in x])

        antiderivation = interior_product

        def hodge_dual(self):
            r"""
            Return the Hodge dual of ``self``.

            The Hodge dual of an element `\alpha` of the exterior algebra is
            defined as `i_{\alpha} \sigma`, where `\sigma` is the volume
            form
            (:meth:`~sage.algebras.clifford_algebra.ExteriorAlgebra.volume_form`)
            and `i_{\alpha}` denotes the antiderivation function with
            respect to `\alpha` (see :meth:`interior_product` for the
            definition of this).

            .. NOTE::

                The Hodge dual of the Hodge dual of a homogeneous element
                `p` of `\Lambda(V)` equals `(-1)^{k(n-k)} p`, where
                `n = \dim V` and `k = \deg(p) = |p|`.

            EXAMPLES::

                sage: E.<x,y,z> = ExteriorAlgebra(QQ)
                sage: x.hodge_dual()
                y^z
                sage: (x*z).hodge_dual()
                -y
                sage: (x*y*z).hodge_dual()
                1
                sage: [a.hodge_dual().hodge_dual() for a in E.basis()]
                [1, x, y, z, x^y, x^z, y^z, x^y^z]
                sage: (x + x*y).hodge_dual()
                y^z + z
                sage: (x*z + x*y*z).hodge_dual()
                -y + 1
                sage: E = ExteriorAlgebra(QQ, 'wxyz')
                sage: [a.hodge_dual().hodge_dual() for a in E.basis()]
                [1, -w, -x, -y, -z, w^x, w^y, w^z, x^y, x^z, y^z,
                 -w^x^y, -w^x^z, -w^y^z, -x^y^z, w^x^y^z]
            """
            volume_form = self.parent().volume_form()
            return volume_form.interior_product(self)

        def constant_coefficient(self):
            """
            Return the constant coefficient of ``self``.

            .. TODO::

                Define a similar method for general Clifford algebras once
                the morphism to exterior algebras is implemented.

            EXAMPLES::

                sage: E.<x,y,z> = ExteriorAlgebra(QQ)
                sage: elt = 5*x + y + x*z + 10
                sage: elt.constant_coefficient()
                10
                sage: x.constant_coefficient()
                0
            """
            return self._monomial_coefficients.get(self.parent().one_basis(),
                                                   self.base_ring().zero())

        def scalar(self, other):
            r"""
            Return the standard scalar product of ``self`` with ``other``.

            The standard scalar product of `x, y \in \Lambda(V)` is
            defined by `\langle x, y \rangle = \langle x^t y \rangle`, where
            `\langle a \rangle` denotes the degree-0 term of `a`, and where
            `x^t` denotes the transpose
            (:meth:`~sage.algebras.clifford_algebra.CliffordAlgebraElement.transpose`)
            of `x`.

            .. TODO::

                Define a similar method for general Clifford algebras once
                the morphism to exterior algebras is implemented.

            EXAMPLES::

                sage: E.<x,y,z> = ExteriorAlgebra(QQ)
                sage: elt = 5*x + y + x*z
                sage: elt.scalar(z + 2*x)
                0
                sage: elt.transpose() * (z + 2*x)
                -2*x^y + 5*x^z + y^z
            """
            return (self.transpose() * other).constant_coefficient()

#####################################################################
## Differentials

class ExteriorAlgebraDifferential(ModuleMorphismByLinearity, UniqueRepresentation):
    r"""
    Internal class to store the data of a boundary or coboundary of
    an exterior algebra `\Lambda(L)` defined by the structure
    coefficients of a Lie algebra `L`.

    See :class:`ExteriorAlgebraBoundary` and
    :class:`ExteriorAlgebraCoboundary` for the actual classes, which
    inherit from this.

    .. WARNING::

        This is not a general class for differentials on the exterior
        algebra.
    """
    @staticmethod
    def __classcall__(cls, E, s_coeff):
        """
        Standardize the structure coefficients to ensure a unique
        representation.

        EXAMPLES::

            sage: from sage.algebras.clifford_algebra import ExteriorAlgebraDifferential
            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: par1 = ExteriorAlgebraDifferential(E, {(0,1): z, (1,2): x, (2,0): y})
            sage: par2 = ExteriorAlgebraDifferential(E, {(0,1): z, (1,2): x, (0,2): -y})
            sage: par3 = ExteriorAlgebraDifferential(E, {(1,0): {2:-1}, (1,2): {0:1}, (2,0):{1:1}})
            sage: par1 is par2 and par2 is par3
            True

            sage: par4 = ExteriorAlgebraDifferential(E, {})
            sage: par5 = ExteriorAlgebraDifferential(E, {(1,0): 0, (1,2): {}, (0,2): E.zero()})
            sage: par6 = ExteriorAlgebraDifferential(E, {(1,0): 0, (1,2): 0, (0,2): 0})
            sage: par4 is par5 and par5 is par6
            True
        """
        d = {}

        for k,v in dict(s_coeff).iteritems():
            if not v: # Strip terms with 0
                continue

            if isinstance(v, dict):
                R = E.base_ring()
                v = E._from_dict({(i,): R(c) for i,c in v.iteritems()})
            else:
                # Make sure v is in ``E``
                v = E(v)
                # It's okay if v.degree results in an error
                #   (we'd throw a similar error) unless v == 0 (which
                #   is what v.list() is testing for)
                if v.list() and v.degree() != 1:
                    raise ValueError("elements must be degree 1")

            if k[0] < k[1]:
                d[tuple(k)] = v
            else:
                d[(k[1], k[0])] = -v

        from sage.sets.family import Family
        return super(ExteriorAlgebraDifferential, cls).__classcall__(cls, E, Family(d))

    def __init__(self, E, s_coeff):
        """
        Initialize ``self``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: par = E.boundary({(0,1): z, (1,2):x, (2,0):y})
            sage: TestSuite(par).run() # known bug - morphisms are properly in a category
        """
        self._s_coeff = s_coeff

        # Technically this preserves the grading but with a shift of -1
        cat = AlgebrasWithBasis(E.base_ring())
        ModuleMorphismByLinearity.__init__(self, domain=E, codomain=E, category=cat)

    def homology(self, deg=None, **kwds):
        """
        Return the homology determined by ``self``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: par = E.boundary({(0,1): z, (1,2): x, (2,0): y})
            sage: par.homology()
            {0: Vector space of dimension 1 over Rational Field,
             1: Vector space of dimension 0 over Rational Field,
             2: Vector space of dimension 0 over Rational Field,
             3: Vector space of dimension 1 over Rational Field}
            sage: d = E.coboundary({(0,1): z, (1,2): x, (2,0): y})
            sage: d.homology()
            {0: Vector space of dimension 1 over Rational Field,
             1: Vector space of dimension 0 over Rational Field,
             2: Vector space of dimension 0 over Rational Field,
             3: Vector space of dimension 1 over Rational Field}
        """
        return self.chain_complex().homology(deg, **kwds)

class ExteriorAlgebraBoundary(ExteriorAlgebraDifferential):
    r"""
    The boundary `\partial` of an exterior algebra `\Lambda(L)` defined
    by the structure coefficients of `L`.

    Let `L` be a Lie algebra. We give the exterior algebra
    `E = \Lambda(L)` a chain complex structure by considering a
    differential `\partial : \Lambda^{k+1}(L) \to \Lambda^k(L)` defined by

    .. MATH::

        \partial(x_1 \wedge x_2 \wedge \cdots \wedge x_{k+1})
        = \sum_{i < j} (-1)^{i+j+1}
        [x_i, x_j] \wedge x_1 \wedge \cdots \wedge \hat{x}_i \wedge \cdots
        \wedge \hat{x}_j \wedge \cdots \wedge x_{k+1}

    where `\hat{x}_i` denotes a missing index. The corresponding homology is
    the Lie algebra homology.

    INPUT:

    - ``E`` -- an exterior algebra of a vector space `L`
    - ``s_coeff`` -- a dictionary whose keys are in `I \times I`, where
      `I` is the index set of the basis of the vector space `L`, and whose
      values can be coerced into 1-forms (degree 1 elements) in ``E``;
      this dictionary will be used to define the Lie algebra structure
      on `L` (indeed, the `i`-th coordinate of the Lie bracket of the
      `j`-th and `k`-th basis vectors of `L` for `j < k` is set to be
      the value at the key `(j, k)` if this key appears in ``s_coeff``,
      or otherwise the negated of the value at the key `(k, j)`)

    .. WARNING::

        The values of ``s_coeff`` are supposed to be coercible into
        1-forms in ``E``; but they can also be dictionaries themselves
        (in which case they are interpreted as giving the coordinates of
        vectors in ``L``). In the interest of speed, these dictionaries
        are not sanitized or checked.

    .. WARNING::

        For any two distinct elements `i` and `j` of `I`, the dictionary
        ``s_coeff`` must have only one of the pairs `(i, j)` and
        `(j, i)` as a key. This is not checked.

    EXAMPLES:

    We consider the differential given by Lie algebra given by the cross
    product `\times` of `\RR^3`::

        sage: E.<x,y,z> = ExteriorAlgebra(QQ)
        sage: par = E.boundary({(0,1): z, (1,2): x, (2,0): y})
        sage: par(x)
        0
        sage: par(x*y)
        z
        sage: par(x*y*z)
        0
        sage: par(x+y-y*z+x*y)
        -x + z
        sage: par(E.zero())
        0

    We check that `\partial \circ \partial = 0`::

        sage: p2 = par * par
        sage: all(p2(b) == 0 for b in E.basis())
        True

    Another example: the Lie algebra `\mathfrak{sl}_2`, which has a
    basis `e,f,h` satisfying `[h,e] = 2e`, `[h,f] = -2f`, and `[e,f] = h`::

        sage: E.<e,f,h> = ExteriorAlgebra(QQ)
        sage: par = E.boundary({(0,1): h, (2,1): -2*f, (2,0): 2*e})
        sage: par(E.zero())
        0
        sage: par(e)
        0
        sage: par(e*f)
        h
        sage: par(f*h)
        2*f
        sage: par(h*f)
        -2*f
        sage: C = par.chain_complex(); C
        Chain complex with at most 4 nonzero terms over Rational Field
        sage: ascii_art(C)
                                  [ 0 -2  0]       [0]
                                  [ 0  0  2]       [0]
                    [0 0 0]       [ 1  0  0]       [0]
         0 <-- C_0 <-------- C_1 <----------- C_2 <---- C_3 <-- 0
        sage: C.homology()
        {0: Vector space of dimension 1 over Rational Field,
         1: Vector space of dimension 0 over Rational Field,
         2: Vector space of dimension 0 over Rational Field,
         3: Vector space of dimension 1 over Rational Field}

    Over the integers::

        sage: C = par.chain_complex(R=ZZ); C
        Chain complex with at most 4 nonzero terms over Integer Ring
        sage: ascii_art(C)
                                  [ 0 -2  0]       [0]
                                  [ 0  0  2]       [0]
                    [0 0 0]       [ 1  0  0]       [0]
         0 <-- C_0 <-------- C_1 <----------- C_2 <---- C_3 <-- 0
        sage: C.homology()
        {0: Z, 1: C2 x C2, 2: 0, 3: Z}

    REFERENCES:

    - :wikipedia:`Exterior_algebra#Lie_algebra_homology`
    """
    def _repr_type(self):
        """
        TESTS::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: par = E.boundary({(0,1): z, (1,2): x, (2,0): y})
            sage: par._repr_type()
            'Boundary'
        """
        return "Boundary"

    def _on_basis(self, m):
        """
        Return the differential on the basis element indexed by ``m``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: par = E.boundary({(0,1): z, (1,2): x, (2,0): y})
            sage: par._on_basis(())
            0
            sage: par._on_basis((0,))
            0
            sage: par._on_basis((0,1))
            z
            sage: par._on_basis((0,2))
            -y
            sage: par._on_basis((0,1,2))
            0
        """
        E = self.domain()
        sc = self._s_coeff
        keys = sc.keys()
        return E.sum((-1)**b * sc[(i,j)]
                      * E.monomial(m[:a] + m[a+1:a+b+1] + m[a+b+2:])
                     for a,i in enumerate(m) for b,j in enumerate(m[a+1:]) if (i,j) in keys)

    @cached_method
    def chain_complex(self, R=None):
        """
        Return the chain complex over ``R`` determined by ``self``.

        INPUT:

        - ``R`` -- the base ring; the default is the base ring of
          the exterior algebra

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: par = E.boundary({(0,1): z, (1,2): x, (2,0): y})
            sage: C = par.chain_complex(); C
            Chain complex with at most 4 nonzero terms over Rational Field
            sage: ascii_art(C)
                                      [ 0  0  1]       [0]
                                      [ 0 -1  0]       [0]
                        [0 0 0]       [ 1  0  0]       [0]
             0 <-- C_0 <-------- C_1 <----------- C_2 <---- C_3 <-- 0

        TESTS:

        This still works in degree `1`::

            sage: E.<x> = ExteriorAlgebra(QQ)
            sage: par = E.boundary({})
            sage: C = par.chain_complex(); C
            Chain complex with at most 2 nonzero terms over Rational Field
            sage: ascii_art(C)
                        [0]
             0 <-- C_0 <---- C_1 <-- 0

        Also in degree `0`::

            sage: E = ExteriorAlgebra(QQ, 0)
            sage: par = E.boundary({})
            sage: C = par.chain_complex(); C
            Chain complex with at most 1 nonzero terms over Rational Field
            sage: ascii_art(C)
             0 <-- C_0 <-- 0
        """
        from sage.homology.chain_complex import ChainComplex
        from sage.matrix.constructor import Matrix
        E = self.domain()
        n = E.ngens()
        if R is None:
            R = E.base_ring()

        if n == 0:
            # Special case because there are no matrices and thus the
            # ChainComplex constructor needs the dimension of the
            # 0th degree space explicitly given.
            return ChainComplex({1: Matrix(R, [[]])}, degree=-1)
            # If you are reading this because you changed something about
            # the ChainComplex constructor and the doctests are failing:
            # This should return a chain complex with degree -1 and
            # only one nontrivial module, namely a free module of rank 1,
            # situated in degree 0.

        # Group the basis into degrees
        basis_by_deg = {deg: [] for deg in range(n+1)}
        for b in E.basis().keys():
            basis_by_deg[len(b)].append(b)

        # Construct the transition matrices
        data = {}
        prev_basis = basis_by_deg[0]
        for deg in range(1,n+1):
            # Make sure within each basis we're sorted by lex
            basis = sorted(basis_by_deg[deg])
            mat = []
            for b in basis:
                ret = self._on_basis(b)
                mat.append([ret[p] for p in prev_basis])
            data[deg] = Matrix(mat).transpose().change_ring(R)
            prev_basis = basis

        return ChainComplex(data, degree=-1)

class ExteriorAlgebraCoboundary(ExteriorAlgebraDifferential):
    r"""
    The coboundary `d` of an exterior algebra `\Lambda(L)` defined
    by the structure coefficients of a Lie algebra `L`.

    Let `L` be a Lie algebra. We endow its exterior algebra
    `E = \Lambda(L)` with a cochain complex structure by considering a
    differential `d : \Lambda^k(L) \to \Lambda^{k+1}(L)` defined by

    .. MATH::

        d x_i = \sum_{j < k} s_{jk}^i x_j x_k,

    where `(x_1, x_2, \ldots, x_n)` is a basis of `L`, and where
    `s_{jk}^i` is the `x_i`-coordinate of the Lie bracket `[x_j, x_k]`.

    The corresponding cohomology is the Lie algebra cohomology of `L`.

    This can also be thought of as the exterior derivative, in which case
    the resulting cohomology is the de Rham cohomology of a manifold whose
    exterior algebra of differential forms is ``E``.

    INPUT:

    - ``E`` -- an exterior algebra of a vector space `L`
    - ``s_coeff`` -- a dictionary whose keys are in `I \times I`, where
      `I` is the index set of the basis of the vector space `L`, and whose
      values can be coerced into 1-forms (degree 1 elements) in ``E``;
      this dictionary will be used to define the Lie algebra structure
      on `L` (indeed, the `i`-th coordinate of the Lie bracket of the
      `j`-th and `k`-th basis vectors of `L` for `j < k` is set to be
      the value at the key `(j, k)` if this key appears in ``s_coeff``,
      or otherwise the negated of the value at the key `(k, j)`)

    .. WARNING::

        For any two distinct elements `i` and `j` of `I`, the dictionary
        ``s_coeff`` must have only one of the pairs `(i, j)` and
        `(j, i)` as a key. This is not checked.

    EXAMPLES:

    We consider the differential coming from the Lie algebra given by the
    cross product `\times` of `\RR^3`::

        sage: E.<x,y,z> = ExteriorAlgebra(QQ)
        sage: d = E.coboundary({(0,1): z, (1,2): x, (2,0): y})
        sage: d(x)
        y^z
        sage: d(y)
        -x^z
        sage: d(x+y-y*z)
        -x^z + y^z
        sage: d(x*y)
        0
        sage: d(E.one())
        0
        sage: d(E.zero())
        0

    We check that `d \circ d = 0`::

        sage: d2 = d * d
        sage: all(d2(b) == 0 for b in E.basis())
        True

    Another example: the Lie algebra `\mathfrak{sl}_2`, which has a
    basis `e,f,h` satisfying `[h,e] = 2e`, `[h,f] = -2f`, and `[e,f] = h`::

        sage: E.<e,f,h> = ExteriorAlgebra(QQ)
        sage: d = E.coboundary({(0,1): h, (2,1): -2*f, (2,0): 2*e})
        sage: d(E.zero())
        0
        sage: d(e)
        -2*e^h
        sage: d(f)
        2*f^h
        sage: d(h)
        e^f
        sage: d(e*f)
        0
        sage: d(f*h)
        0
        sage: d(e*h)
        0
        sage: C = d.chain_complex(); C
        Chain complex with at most 4 nonzero terms over Rational Field
        sage: ascii_art(C)
                                  [ 0  0  1]       [0]
                                  [-2  0  0]       [0]
                    [0 0 0]       [ 0  2  0]       [0]
         0 <-- C_3 <-------- C_2 <----------- C_1 <---- C_0 <-- 0
        sage: C.homology()
        {0: Vector space of dimension 1 over Rational Field,
         1: Vector space of dimension 0 over Rational Field,
         2: Vector space of dimension 0 over Rational Field,
         3: Vector space of dimension 1 over Rational Field}

    Over the integers::

        sage: C = d.chain_complex(R=ZZ); C
        Chain complex with at most 4 nonzero terms over Integer Ring
        sage: ascii_art(C)
                                  [ 0  0  1]       [0]
                                  [-2  0  0]       [0]
                    [0 0 0]       [ 0  2  0]       [0]
         0 <-- C_3 <-------- C_2 <----------- C_1 <---- C_0 <-- 0
        sage: C.homology()
        {0: Z, 1: 0, 2: C2 x C2, 3: Z}

    REFERENCES:

    - :wikipedia:`Exterior_algebra#Differential_geometry`
    """
    def __init__(self, E, s_coeff):
        """
        Initialize ``self``.

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: d = E.coboundary({(0,1): z, (1,2):x, (2,0):y})
            sage: TestSuite(d).run() # known bug - morphisms are properly in a category
        """
        # Construct the dictionary of costructure coefficients, i.e. given
        # [x_j, x_k] = \sum_i s_{jk}^i x_i, we get x^i |-> \sum_{j<k} s_{jk}^i x^j x^k.
        # This dictionary might contain 0 values and might also be missing
        # some keys (both times meaning that the respective `s_{jk}^i` are
        # zero for all `j` and `k`).
        self._cos_coeff = {}
        zero = E.zero()
        B = E.basis()
        for k,v in dict(s_coeff).iteritems():
            k = B[k]
            for m,c in v:
                self._cos_coeff[m] = self._cos_coeff.get(m, zero) + c * k
        ExteriorAlgebraDifferential.__init__(self, E, s_coeff)

    def _repr_type(self):
        """
        TESTS::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: d = E.coboundary({(0,1): z, (1,2): x, (2,0): y})
            sage: d._repr_type()
            'Coboundary'
        """
        return "Coboundary"

    def _on_basis(self, m):
        """
        Return the differential on the basis element indexed by ``m``.

        EXAMPLES:

        The vector space `\RR^3` made into a Lie algebra using the
        cross product::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: d = E.coboundary({(0,1): z, (1,2): x, (2,0): y})
            sage: d._on_basis(())
            0
            sage: d._on_basis((0,))
            y^z
            sage: d._on_basis((1,))
            -x^z
            sage: d._on_basis((2,))
            x^y
            sage: d._on_basis((0,1))
            0
            sage: d._on_basis((0,2))
            0
            sage: d._on_basis((0,1,2))
            0
        """
        E = self.domain()
        cc = self._cos_coeff
        keys = cc.keys()
        return E.sum((-1)**a * E.monomial(m[:a]) * cc[(i,)] * E.monomial(m[a+1:])
                     for a,i in enumerate(m) if (i,) in keys)

    @cached_method
    def chain_complex(self, R=None):
        """
        Return the chain complex over ``R`` determined by ``self``.

        INPUT:

        - ``R`` -- the base ring; the default is the base ring of
          the exterior algebra

        EXAMPLES::

            sage: E.<x,y,z> = ExteriorAlgebra(QQ)
            sage: d = E.coboundary({(0,1): z, (1,2): x, (2,0): y})
            sage: C = d.chain_complex(); C
            Chain complex with at most 4 nonzero terms over Rational Field
            sage: ascii_art(C)
                                      [ 0  0  1]       [0]
                                      [ 0 -1  0]       [0]
                        [0 0 0]       [ 1  0  0]       [0]
             0 <-- C_3 <-------- C_2 <----------- C_1 <---- C_0 <-- 0

        TESTS:

        This still works in degree `1`::

            sage: E.<x> = ExteriorAlgebra(QQ)
            sage: d = E.coboundary({})
            sage: C = d.chain_complex(); C
            Chain complex with at most 2 nonzero terms over Rational Field
            sage: ascii_art(C)
                        [0]
             0 <-- C_1 <---- C_0 <-- 0

        Also in degree `0`::

            sage: E = ExteriorAlgebra(QQ, 0)
            sage: d = E.coboundary({})
            sage: C = d.chain_complex(); C
            Chain complex with at most 1 nonzero terms over Rational Field
            sage: ascii_art(C)
             0 <-- C_0 <-- 0
        """
        from sage.homology.chain_complex import ChainComplex
        from sage.matrix.constructor import Matrix
        E = self.domain()
        n = E.ngens()
        if R is None:
            R = E.base_ring()

        if n == 0:
            # Special case because there are no matrices and thus the
            # ChainComplex constructor needs the dimension of the
            # 0th degree space explicitly given.
            return ChainComplex({-1: Matrix(R, [[]])}, degree=1)
            # If you are reading this because you changed something about
            # the ChainComplex constructor and the doctests are failing:
            # This should return a chain complex with degree 1 and
            # only one nontrivial module, namely a free module of rank 1,
            # situated in degree 0.

        # Group the basis into degrees
        basis_by_deg = {deg: [] for deg in range(n+1)}
        for b in E.basis().keys():
            basis_by_deg[len(b)].append(b)

        # Construct the transition matrices
        data = {}
        basis = basis_by_deg[0]
        for deg in range(n):
            # Make sure within each basis we're sorted by lex
            next_basis = sorted(basis_by_deg[deg+1])
            mat = []
            for b in basis:
                ret = self._on_basis(b)
                mat.append([ret[p] for p in next_basis])
            data[deg] = Matrix(mat).transpose().change_ring(R)
            basis = next_basis

        return ChainComplex(data, degree=1)

