#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math

def mat_mul(A, B):
    n, m = len(A), len(A[0])
    p = len(B[0])
    C = [[sum(A[i][k]*B[k][j] for k in range(m)) for j in range(p)] for i in range(n)]
    return C

def mat_add(A, B):
    return [[A[i][j]+B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def mat_sub(A, B):
    return [[A[i][j]-B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def mat_scalar(A, s):
    return [[A[i][j]*s for j in range(len(A[0]))] for i in range(len(A))]

def mat_transpose(A):
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]

def mat_det(A):
    n = len(A)
    if n == 1: return A[0][0]
    if n == 2: return A[0][0]*A[1][1] - A[0][1]*A[1][0]
    d = 0
    for j in range(n):
        minor = [[A[i][k] for k in range(n) if k != j] for i in range(1, n)]
        d += ((-1)**j) * A[0][j] * mat_det(minor)
    return d

def mat_inverse(A):
    n = len(A)
    aug = [A[i][:] + [1 if i==j else 0 for j in range(n)] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        if abs(aug[col][col]) < 1e-12:
            return None
        factor = aug[col][col]
        aug[col] = [v/factor for v in aug[col]]
        for row in range(n):
            if row != col:
                f = aug[row][col]
                aug[row] = [aug[row][k] - f*aug[col][k] for k in range(2*n)]
    return [aug[i][n:] for i in range(n)]

def mat_rref(A):
    A = [row[:] for row in A]
    n, m = len(A), len(A[0])
    row = 0
    for col in range(m):
        pivot = next((r for r in range(row, n) if abs(A[r][col]) > 1e-12), None)
        if pivot is None: continue
        A[row], A[pivot] = A[pivot], A[row]
        factor = A[row][col]
        A[row] = [v/factor for v in A[row]]
        for r in range(n):
            if r != row:
                f = A[r][col]
                A[r] = [A[r][k] - f*A[row][k] for k in range(m)]
        row += 1
    return A

def fmt_mat(M, decimals=4):
    lines = []
    for row in M:
        lines.append("  ".join(f"{v:>10.{decimals}g}" for v in row))
    return "\n".join(lines)

class MatrixCalcWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Matrix Calculator")
        self.set_default_size(900, 620)
        self.build_ui()

    def parse_matrix(self, text):
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        rows = []
        for line in lines:
            parts = line.replace(',', ' ').split()
            rows.append([float(p) for p in parts])
        if not rows: raise ValueError("Empty")
        cols = len(rows[0])
        if any(len(r) != cols for r in rows): raise ValueError("Inconsistent columns")
        return rows

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Matrix Calculator", css_classes=["title"]))

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        a_frame = Gtk.Frame(label="Matrix A")
        scroll_a = Gtk.ScrolledWindow(); scroll_a.set_size_request(260, 140)
        self.a_view = Gtk.TextView(); self.a_view.set_monospace(True)
        self.a_view.get_buffer().set_text("1 2 3\n4 5 6\n7 8 9")
        scroll_a.set_child(self.a_view)
        a_frame.set_child(scroll_a)
        input_box.append(a_frame)

        b_frame = Gtk.Frame(label="Matrix B")
        scroll_b = Gtk.ScrolledWindow(); scroll_b.set_size_request(260, 140)
        self.b_view = Gtk.TextView(); self.b_view.set_monospace(True)
        self.b_view.get_buffer().set_text("9 8 7\n6 5 4\n3 2 1")
        scroll_b.set_child(self.b_view)
        b_frame.set_child(scroll_b)
        input_box.append(b_frame)

        scalar_frame = Gtk.Frame(label="Scalar")
        scalar_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scalar_vbox.set_margin_top(4); scalar_vbox.set_margin_start(4)
        self.scalar_spin = Gtk.SpinButton.new_with_range(-1000, 1000, 0.5)
        self.scalar_spin.set_value(2)
        scalar_vbox.append(self.scalar_spin)
        scalar_frame.set_child(scalar_vbox)
        input_box.append(scalar_frame)
        vbox.append(input_box)

        ops_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ops_box.set_halign(Gtk.Align.CENTER)
        ops = [("A + B", "add"), ("A - B", "sub"), ("A × B", "mul"),
               ("k × A", "scalar"), ("Transpose A", "trans"), ("Det(A)", "det"),
               ("Inverse A", "inv"), ("RREF(A)", "rref"), ("Trace(A)", "trace")]
        for label, op in ops:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self.on_op, op)
            ops_box.append(btn)
        vbox.append(ops_box)

        result_frame = Gtk.Frame(label="Result")
        scroll_r = Gtk.ScrolledWindow(); scroll_r.set_vexpand(True)
        self.result_view = Gtk.TextView(); self.result_view.set_editable(False); self.result_view.set_monospace(True)
        scroll_r.set_child(self.result_view)
        result_frame.set_child(scroll_r)
        vbox.append(result_frame)

    def get_mat(self, view):
        buf = view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        return self.parse_matrix(text)

    def show_result(self, M):
        if isinstance(M, (int, float)):
            self.result_view.get_buffer().set_text(str(M))
        elif isinstance(M, list):
            self.result_view.get_buffer().set_text(fmt_mat(M))
        else:
            self.result_view.get_buffer().set_text(str(M))

    def on_op(self, btn, op):
        try:
            A = self.get_mat(self.a_view)
            if op == "add": self.show_result(mat_add(A, self.get_mat(self.b_view)))
            elif op == "sub": self.show_result(mat_sub(A, self.get_mat(self.b_view)))
            elif op == "mul": self.show_result(mat_mul(A, self.get_mat(self.b_view)))
            elif op == "scalar": self.show_result(mat_scalar(A, self.scalar_spin.get_value()))
            elif op == "trans": self.show_result(mat_transpose(A))
            elif op == "det":
                if len(A) != len(A[0]):
                    raise ValueError("Matrix must be square for determinant")
                d = mat_det(A)
                self.result_view.get_buffer().set_text(f"det(A) = {d:.6g}")
            elif op == "inv":
                if len(A) != len(A[0]):
                    raise ValueError("Matrix must be square for inverse")
                inv = mat_inverse(A)
                if inv is None:
                    self.result_view.get_buffer().set_text("Matrix is singular (no inverse)")
                else:
                    self.show_result(inv)
            elif op == "rref": self.show_result(mat_rref(A))
            elif op == "trace":
                if len(A) != len(A[0]):
                    raise ValueError("Matrix must be square for trace")
                t = sum(A[i][i] for i in range(len(A)))
                self.result_view.get_buffer().set_text(f"trace(A) = {t:.6g}")
        except Exception as e:
            self.result_view.get_buffer().set_text(f"Error: {e}")

class MatrixCalcApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.MatrixCalc")
    def do_activate(self):
        win = MatrixCalcWindow(self); win.present()

def main():
    app = MatrixCalcApp(); app.run(None)

if __name__ == "__main__":
    main()
