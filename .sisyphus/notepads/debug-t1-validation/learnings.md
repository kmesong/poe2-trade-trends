Fixed nesting bug in _is_t1_magic by accessing extended inside item. Fixed breadth bug by limiting mod groups to explicit, fractured, and desecrated. Ensure has_any_mod is only true for targeted groups.
Updated test structure in backend/tests/test_price_analyzer.py to match nested 'item.extended.mods' API response. Added regression test for ignoring implicits in T1 validation.
