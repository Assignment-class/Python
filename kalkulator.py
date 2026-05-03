def tambah(a, b):
  """
  Fungsi ini menerima dua angka dan mengembalikan hasil penjumlahannya.
  """
  return a + b

def kurang(a, b):
  """
  Fungasi ini menerima dua angka dan mengembalikan hasil pengurangannya.
  """
  return a - b

def kali(a, b):
  """
  Fungsi ini menerima dua angka dan mengembalikan hasil perkaliannya.
  """
  return a * b

def bagi(a, b):
  """
  Fungsi ini menerima dua angka dan mengembalikan hasil pembagiannya.
  Jika pembaginya adalah 0, kembalikan string "Error: Pembagian dengan nol".
  """
  if b == 0:
      return "Error: Pembagian dengan nol"
  return a / b
