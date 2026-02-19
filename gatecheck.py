import sys, compileall
ok = compileall.compile_dir('src', quiet=1)
sys.exit(0 if ok else 1)
