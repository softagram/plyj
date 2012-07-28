import unittest

import plyj.parser as plyj
import plyj.model as model

class StatementTest(unittest.TestCase):

    def setUp(self):
        self.parser = plyj.Parser()

    def test_while(self):
        self.assert_stmt('while(foo) return;', model.While('foo', body=model.Return()))
        self.assert_stmt('while(foo) { return; }', model.While('foo', body=[model.Return()]))

        self.assert_stmt('do return; while(foo);', model.DoWhile('foo', body=model.Return()))
        self.assert_stmt('do { return; } while(foo);', model.DoWhile('foo', body=[model.Return()]))

    def test_for(self):
        initializer = model.VariableDeclaration('int', [model.VariableDeclarator(model.Variable('i'), initializer='0')])
        predicate = model.BinaryExpression('<', 'i', '10')
        update = model.Unary('x++', 'i')

        self.assert_stmt('for(;;);', model.For(None, None, None, body=None))
        self.assert_stmt('for(;;) return;', model.For(None, None, None, body=model.Return()))
        self.assert_stmt('for(;;) { return; }', model.For(None, None, None, body=[model.Return()]))
        self.assert_stmt('for(int i=0;;) return;', model.For(initializer, None, None, body=model.Return()))
        self.assert_stmt('for(;i<10;) return;', model.For(None, predicate, None, body=model.Return()))
        self.assert_stmt('for(;;i++) return;', model.For(None, None, [update], body=model.Return()))
        self.assert_stmt('for(int i=0; i<10; i++) return;', model.For(initializer, predicate, [update], body=model.Return()))

        initializer2 = [model.Assignment('=', 'i', '0'), model.Assignment('=', 'j', '2')]
        self.assert_stmt('for(i=0, j=2;;) return;', model.For(initializer2, None, None, body=model.Return()))

        update2 = model.Unary('x++', 'j')
        self.assert_stmt('for(;;i++, j++) return;', model.For(None, None, [update, update2], body=model.Return()))

        self.assert_stmt('for(int i : foo) return;', model.ForEach('int', model.Variable('i'), 'foo', body=model.Return()))

    def test_assert(self):
        self.assert_stmt('assert foo;', model.Assert('foo'))
        self.assert_stmt('assert foo : "bar";', model.Assert('foo', message='"bar"'))

    def test_switch(self):
        default = model.SwitchCase(['default'], body=[model.Return()])

        self.assert_stmt('switch(foo) {}', model.Switch('foo', []))
        self.assert_stmt('switch(foo) { default: return; }', model.Switch('foo', [default]))

        case1 = model.SwitchCase(['1'], [model.Return('1')])
        self.assert_stmt('switch(foo) { case 1: return 1; }', model.Switch('foo', [case1]))
        self.assert_stmt('switch(foo) { case 1: return 1; default: return; }', model.Switch('foo', [case1, default]))

        case12 = model.SwitchCase(['1', '2'], [model.Return('3')])
        self.assert_stmt('switch(foo) { case 1: case 2: return 3; }', model.Switch('foo', [case12]))
        self.assert_stmt('switch(foo) { case 1: case 2: return 3; default: return; }', model.Switch('foo', [case12, default]))

    def test_control_flow(self):
        self.assert_stmt('break;', model.Break())
        self.assert_stmt('break label;', model.Break('label'))

        self.assert_stmt('continue;', model.Continue())
        self.assert_stmt('continue label;', model.Continue('label'))

        self.assert_stmt('return;', model.Return())
        self.assert_stmt('return 1;', model.Return('1'))

        self.assert_stmt('throw foo;', model.Throw('foo'))

    def test_synchronized(self):
        self.assert_stmt('synchronized (foo) { return; }', model.Synchronized('foo', body=[model.Return()]))

    def test_try(self):
        r1 = model.Return('1')
        r2 = model.Return('2')
        r3 = model.Return('3')
        c1 = model.Catch(model.Variable('e'), types=[model.Type('Exception')], block=[r2])
        self.assert_stmt('try { return 1; } catch (Exception e) { return 2; }', model.Try([r1], catches=[c1]))
        self.assert_stmt('try { return 1; } catch (Exception e) { return 2; } finally { return 3; }',
                         model.Try([r1], catches=[c1], _finally=[r3]))
        self.assert_stmt('try { return 1; } finally { return 2; }', model.Try([r1], _finally=[r2]))

        c2 = model.Catch(model.Variable('e'), types=[model.Type('Exception1'), model.Type('Exception2')], block=[r3])
        self.assert_stmt('try { return 1; } catch (Exception1 | Exception2 e) { return 3; }',
                         model.Try([r1], catches=[c2]))
        self.assert_stmt('try { return 1; } catch (Exception e) { return 2; } catch (Exception1 | Exception2 e) { return 3; }',
                         model.Try([r1], catches=[c1, c2]))
        self.assert_stmt('try { return 1; } catch (Exception e) { return 2; } catch (Exception1 | Exception2 e) { return 3; } finally { return 3; }',
                         model.Try([r1], catches=[c1, c2], _finally=[r3]))

        res1 = model.Resource(model.Variable('r'), _type=model.Type('Resource'), initializer='foo')
        res2 = model.Resource(model.Variable('r2'), _type=model.Type('Resource2'), initializer='bar')
        self.assert_stmt('try(Resource r = foo) { return 1; }', model.Try([r1], resources=[res1]))
        self.assert_stmt('try(Resource r = foo;) { return 1; }', model.Try([r1], resources=[res1]))
        self.assert_stmt('try(Resource r = foo; Resource2 r2 = bar) { return 1; }', model.Try([r1], resources=[res1, res2]))
        self.assert_stmt('try(Resource r = foo; Resource2 r2 = bar;) { return 1; }', model.Try([r1], resources=[res1, res2]))
        self.assert_stmt('try(Resource r = foo) { return 1; } catch (Exception e) { return 2; }',
                         model.Try([r1], resources=[res1], catches=[c1]))
        self.assert_stmt('try(Resource r = foo) { return 1; } catch (Exception1 | Exception2 e) { return 3;}',
                         model.Try([r1], resources=[res1], catches=[c2]))
        self.assert_stmt('try(Resource r = foo) { return 1; } catch (Exception e) { return 2; } catch (Exception1 | Exception2 e) { return 3; }',
                         model.Try([r1], resources=[res1], catches=[c1, c2]))
        self.assert_stmt('try(Resource r = foo) { return 1; } finally { return 3; }',
                         model.Try([r1], resources=[res1], _finally=[r3]))
        self.assert_stmt('try(Resource r = foo) { return 1; } catch (Exception e) { return 2; } finally { return 3; }',
                         model.Try([r1], resources=[res1], catches=[c1], _finally=[r3]))
        self.assert_stmt('try(Resource r = foo) { return 1; } catch (Exception e) { return 2; } catch (Exception1 | Exception2 e) { return 3; } finally { return 3; }',
                         model.Try([r1], resources=[res1], catches=[c1, c2], _finally=[r3]))

    def test_if(self):
        self.assert_stmt('if(foo) return;', model.IfThenElse('foo', if_true=model.Return()))
        self.assert_stmt('if(foo) { return; }', model.IfThenElse('foo', if_true=[model.Return()]))

        r1 = model.Return(result='1')
        r2 = model.Return(result='2')
        self.assert_stmt('if(foo) return 1; else return 2;', model.IfThenElse('foo', if_true=r1, if_false=r2))
        self.assert_stmt('if(foo) {return 1;} else return 2;', model.IfThenElse('foo', if_true=[r1], if_false=r2))
        self.assert_stmt('if(foo) return 1; else {return 2;}', model.IfThenElse('foo', if_true=r1, if_false=[r2]))
        self.assert_stmt('if(foo) {return 1;} else {return 2;}', model.IfThenElse('foo', if_true=[r1], if_false=[r2]))

        # test proper nesting, every parser writer's favorite
        self.assert_stmt('if(foo) if(bar) return 1;', model.IfThenElse('foo', if_true=model.IfThenElse('bar', if_true=r1)))
        self.assert_stmt('if(foo) if(bar) return 1; else return 2;',
                         model.IfThenElse('foo', if_true=model.IfThenElse('bar', if_true=r1, if_false=r2)))
        self.assert_stmt('if(foo) return 1; else if(bar) return 2;',
                         model.IfThenElse('foo', if_true=r1, if_false=model.IfThenElse('bar', if_true=r2)))

    def test_variable_declaration(self):
        var_i = model.Variable('i')
        var_i_decltor = model.VariableDeclarator(var_i)
        var_j = model.Variable('j')
        var_j_decltor = model.VariableDeclarator(var_j)

        self.assert_stmt('int i;', model.VariableDeclaration('int', [var_i_decltor]))
        self.assert_stmt('int i, j;', model.VariableDeclaration('int', [var_i_decltor, var_j_decltor]))

        var_i_decltor.initializer = '1'
        self.assert_stmt('int i = 1;', model.VariableDeclaration('int', [var_i_decltor]))
        self.assert_stmt('int i = 1, j;', model.VariableDeclaration('int', [var_i_decltor, var_j_decltor]))

        var_j_decltor.initializer = 'i'
        self.assert_stmt('int i = 1, j = i;', model.VariableDeclaration('int', [var_i_decltor, var_j_decltor]))

        int_ar = model.Type('int', dimensions=1)
        var_i_decltor.initializer = None
        self.assert_stmt('int[] i;', model.VariableDeclaration(int_ar, [var_i_decltor]))

    def test_array(self):
        var_i = model.Variable('i')
        var_i_decltor = model.VariableDeclarator(var_i)
        var_j = model.Variable('j')
        var_j_decltor = model.VariableDeclarator(var_j)

        int_ar = model.Type('int', dimensions=1)

        arr_init = model.ArrayInitializer(['1', '3'])
        var_i_decltor.initializer = arr_init
        self.assert_stmt('int[] i = {1, 3};', model.VariableDeclaration(int_ar, [var_i_decltor]))

        arr_creation = model.ArrayCreation('int', dimensions=[None], initializer=arr_init)
        var_i_decltor.initializer = arr_creation
        self.assert_stmt('int[] i = new int[] {1, 3};', model.VariableDeclaration(int_ar, [var_i_decltor]))

        arr_creation.dimensions = ['2']
        self.assert_stmt('int[] i = new int[2] {1, 3};', model.VariableDeclaration(int_ar, [var_i_decltor]))

    def assert_stmt(self, stmt, result):
        s = self.parser.parse_statement(stmt)
        self.assertEqual(s, result, 'for {} got {}, expected {}'.format(stmt, s, result))
