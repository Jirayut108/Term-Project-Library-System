import os
from tabulate import tabulate
from datetime import datetime, timedelta

# Base folder for data files (same folder as script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

def get_path(filename):
    return os.path.join(BASE_DIR, filename)

# ------------ Utility ------------
def read_file(filename, min_fields=None):
    """อ่านไฟล์แล้วคืนรายการเป็น list of list
    ถ้ามี min_fields จะเติมช่องว่างให้ครบความยาวนั้นเพื่อหลีกเลี่ยง IndexError
    """
    filepath = get_path(filename)
    if not os.path.exists(filepath):
        return []
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if min_fields and len(parts) < min_fields:
                parts += [""] * (min_fields - len(parts))
            records.append(parts)
    return records


def write_file(filename, records):
    filepath = get_path(filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for rec in records:
                rec = [str(x) for x in rec]
                f.write("|".join(rec) + "\n")
        return True
    except OSError as e:
        print(f"✘ ข้อผิดพลาดในการเขียนไฟล์ {filename}: {e}")
        return False


def get_next_id(records):
    if not records:
        return 1
    ids = []
    for r in records:
        try:
            if r and r[-1] == "A":
                ids.append(int(r[0]))
        except Exception:
            continue
    return max(ids) + 1 if ids else 1


def find_free_slot(records):
    for i, r in enumerate(records):
        if r and r[-1] == "D":
            return i
    return None


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def calculate_fine(borrow_date, return_date, actual_return_date=None):
    try:
        due_date = datetime.strptime(return_date, "%d/%m/%Y")
        if actual_return_date:
            actual = datetime.strptime(actual_return_date, "%d/%m/%Y")
            days_late = (actual - due_date).days
        else:
            days_late = (datetime.now() - due_date).days
        return max(0, days_late * 5)
    except Exception:
        return 0


def ensure_min_len(lst, n):
    while len(lst) < n:
        lst.append("")

# Helpers to get names/titles
def get_book_title(book_id):
    books = read_file("books.txt", min_fields=5)
    return next((b[1] for b in books if b and b[0].strip() == book_id and b[-1] == "A"), "ไม่ทราบชื่อหนังสือ")


def get_member_name(member_id):
    members = read_file("members.txt", min_fields=4)
    return next((m[1] for m in members if m and m[0].strip() == member_id and m[-1] == "A"), "ไม่ทราบชื่อ")

# เพิ่มฟังก์ชันนับจำนวนหนังสือที่ถูกยืมอยู่
def get_borrowed_count(book_id):
    """นับจำนวนเล่มของหนังสือที่กำลังถูกยืมอยู่"""
    borrow_items = read_file("borrow_items.txt", min_fields=6)
    count = 0
    for bi in borrow_items:
        try:
            if bi and bi[-1] == "A" and bi[2].strip() == book_id and bi[3].strip() == "กำลังยืม":
                count += 1
        except Exception:
            continue
    return count

# เพิ่มฟังก์ชันเช็คสถานะหนังสือ
def get_book_borrow_status(book_id):
    """เช็คว่าหนังสือกำลังถูกยืมอยู่หรือไม่"""
    borrow_items = read_file("borrow_items.txt", min_fields=6)
    for bi in borrow_items:
        try:
            if bi and bi[-1] == "A" and bi[2].strip() == book_id and bi[3].strip() == "กำลังยืม":
                return "ถูกยืม"
        except Exception:
            continue
    return "ว่าง"

# ------------ CRUD Template ------------
def add_record(filename, fields):
    records = read_file(filename)
    slot = find_free_slot(records)
    new_id = str(get_next_id(records))
    data = [new_id] + [str(x) for x in fields] + ["A"]
    if slot is not None:
        records[slot] = data
    else:
        records.append(data)
    ok = write_file(filename, records)
    if ok:
        print("✔ บันทึกข้อมูลเรียบร้อย")
    return new_id


def view_records(filename, headers, min_fields=0):
    records = read_file(filename, min_fields=min_fields if min_fields > 0 else None)
    print("\n" + "="*40)
    print(" | ".join(headers))
    print("="*40)
    for r in records:
        if r and r[-1] == "A":
            # ไม่แสดงคอลัมน์ Status สุดท้าย
            display_record = r[:-1]  # เอา status ออก
            print(" | ".join(display_record))
    print("="*40)


def update_record(filename, record_id, new_fields):
    records = read_file(filename)
    for i, r in enumerate(records):
        if r and r[0] == record_id and r[-1] == "A":
            records[i] = [record_id] + [str(x) for x in new_fields] + ["A"]
            write_file(filename, records)
            print("✔ แก้ไขข้อมูลเรียบร้อย")
            return
    print("✘ ไม่พบข้อมูล")


def delete_record(filename, record_id):
    records = read_file(filename)
    for i, r in enumerate(records):
        if r and r[0] == record_id and r[-1] == "A":
            records[i][-1] = "D"
            write_file(filename, records)
            print("✔ ลบข้อมูลเรียบร้อย (Free-list)")
            return
    print("✘ ไม่พบข้อมูล")

# ------------ Specific Functions ------------
def add_book():
    title = input("ชื่อหนังสือ: ").strip()
    author = input("ผู้แต่ง: ").strip()
    while True:
        try:
            total_copies = int(input("จำนวนเล่ม: ").strip())
            if total_copies <= 0:
                print("✘ จำนวนเล่มต้องมากกว่า 0")
                continue
            break
        except ValueError:
            print("✘ กรุณาใส่ตัวเลข")
    add_record("books.txt", [title, author, total_copies])


def view_books():
    """แสดงรายการหนังสือพร้อมสถานะว่าง/ถูกยืม"""
    records = read_file("books.txt", min_fields=5)
    print("\n" + "="*80)
    print(" | ".join(["BookID", "Title", "Author", "Total Copies", "Available"]))
    print("="*80)
    for r in records:
        if r and r[-1] == "A":
            total_copies = int(r[3]) if r[3].isdigit() else 0
            borrowed_count = get_borrowed_count(r[0])
            available_copies = total_copies - borrowed_count
            print(" | ".join([r[0], r[1], r[2], str(total_copies), str(available_copies)]))
    print("="*80)


def add_member():
    name = input("ชื่อสมาชิก: ").strip()
    phone = input("เบอร์โทร: ").strip()
    add_record("members.txt", [name, phone])


def view_members():
    view_records("members.txt", ["MemberID", "Name", "Phone"], min_fields=4)

# ยืมหลายเล่ม (แก้ไขให้รองรับหนังสือหลายเล่มและจำกัดการยืมไม่เกิน 3 เล่ม)
def check_book_availability(book_id):
    """เช็คว่าหนังสือมีเล่มว่างหรือไม่"""
    books = read_file("books.txt", min_fields=5)
    book = next((b for b in books if b and b[0].strip() == book_id and b[-1] == "A"), None)
    if not book:
        return False
    
    total_copies = int(book[3]) if book[3].isdigit() else 0
    borrowed_count = get_borrowed_count(book_id)
    return borrowed_count < total_copies


def check_member_exists(member_id):
    members = read_file("members.txt", min_fields=4)
    return any(m and m[0].strip() == member_id and m[-1] == "A" for m in members)


def check_book_exists(book_id):
    books = read_file("books.txt", min_fields=5)
    return any(b and b[0].strip() == book_id and b[-1] == "A" for b in books)


def show_members_list():
    """แสดงรายการสมาชิกทั้งหมด"""
    records = read_file("members.txt", min_fields=4)
    active_members = []
    
    for r in records:
        if r and r[-1] == "A":
            active_members.append([r[0], r[1], r[2]])
    
    if active_members:
        print("\n👥 รายการสมาชิก:")
        print(tabulate(active_members, headers=["MemberID","ชื่อสมาชิก","เบอร์โทร"], tablefmt="grid"))
    else:
        print("ไม่มีสมาชิกในระบบ")

def show_available_books():
    """แสดงรายการหนังสือที่มีเล่มว่างให้ยืม"""
    records = read_file("books.txt", min_fields=5)
    available_books = []
    
    for r in records:
        if r and r[-1] == "A":
            total_copies = int(r[3]) if r[3].isdigit() else 0
            borrowed_count = get_borrowed_count(r[0])
            available_copies = total_copies - borrowed_count
            if available_copies > 0:
                available_books.append([r[0], r[1], r[2], str(available_copies)])
    
    if available_books:
        print("\n📚 หนังสือที่พร้อมให้ยืม:")
        print(tabulate(available_books, headers=["BookID","ชื่อหนังสือ","ผู้แต่ง","เล่มว่าง"], tablefmt="grid"))
    else:
        print("ไม่มีหนังสือที่พร้อมให้ยืม")

def add_borrow():
    # แสดงรายการสมาชิกก่อน
    show_members_list()
    
    member_id = input("\nรหัสสมาชิก: ").strip()
    if not check_member_exists(member_id):
        print("✘ ไม่พบสมาชิกในระบบ")
        return

    # แสดงรายการหนังสือที่มีให้ยืม
    show_available_books()
    
    print("\nกรอก BookID ที่ต้องการยืม (พิมพ์ 'done' เมื่อเสร็จ หรือ 'cancel' เพื่อยกเลิก):")
    print("หมายเหตุ: สามารถยืมได้ไม่เกิน 3 เล่ม")
    selected_books = []
    while True:
        if len(selected_books) >= 3:
            print("⚠️ ยืมครบ 3 เล่มแล้ว (จำกัด 3 เล่มต่อครั้ง)")
            break
            
        book_id = input(f"BookID ({len(selected_books)+1}/3): ").strip()
        if book_id.lower() == "done":
            break
        if book_id.lower() == "cancel":
            print("❌ ยกเลิกรายการยืมเรียบร้อย (ไม่มีการบันทึกข้อมูล)")
            return
        if not check_book_exists(book_id):
            print("✘ ไม่พบหนังสือในระบบ")
            continue
        if not check_book_availability(book_id):
            print("✘ หนังสือเล่มนี้ไม่มีเล่มว่าง")
            continue
        
        # แสดงข้อมูลหนังสือและจำนวนที่ว่าง
        books = read_file("books.txt", min_fields=5)
        book = next((b for b in books if b and b[0].strip() == book_id and b[-1] == "A"), None)
        if book:
            total_copies = int(book[3]) if book[3].isdigit() else 0
            borrowed_count = get_borrowed_count(book_id)
            available_copies = total_copies - borrowed_count
            print(f"✔ เพิ่มหนังสือ {get_book_title(book_id)} (เหลือ {available_copies-1} เล่ม)")
        
        selected_books.append(book_id)

    if not selected_books:
        print("✘ ไม่มีหนังสือที่เลือก ยกเลิกรายการ")
        return

    # ตอนนี้เพิ่งถามวันที่
    borrow_date = input("วันที่ยืม (dd/mm/yyyy) (หรือพิมพ์ 'cancel' เพื่อยกเลิก): ").strip()
    if borrow_date.lower() == "cancel":
        print("❌ ยกเลิกรายการยืมเรียบร้อย (ไม่มีการบันทึกข้อมูล)")
        return
    if not validate_date(borrow_date):
        print("✘ รูปแบบวันที่ไม่ถูกต้อง")
        return

    borrow_dt = datetime.strptime(borrow_date, "%d/%m/%Y")
    return_dt = borrow_dt + timedelta(days=7)
    return_date = return_dt.strftime("%d/%m/%Y")
    print(f"📅 วันที่ต้องคืน: {return_date}")

    # บันทึกการยืมจริง
    borrow_id = add_record("borrows.txt", [member_id, borrow_date, return_date, "0", "กำลังยืม"])
    for book_id in selected_books:
        add_record("borrow_items.txt", [borrow_id, book_id, "กำลังยืม", "0"])
    print("✔ บันทึกการยืมเรียบร้อย")


def show_active_borrows():
    """แสดงรายการยืมที่ยังไม่คืนครบ"""
    borrows = read_file("borrows.txt", min_fields=7)
    borrow_items = read_file("borrow_items.txt", min_fields=6)
    active_borrows = []
    
    for br in borrows:
        if not br or br[-1] != "A":
            continue
        # เช็คว่ามีหนังสือที่ยังไม่คืนหรือไม่
        has_unreturned = any(bi and len(bi) >= 6 and bi[1] == br[0] and bi[3].strip() == "กำลังยืม" and bi[-1] == "A" for bi in borrow_items)
        if has_unreturned:
            member_name = get_member_name(br[1])
            borrow_date = br[2]
            return_date = br[3]
            
            # หาชื่อหนังสือที่ยังยืมอยู่
            book_titles = []
            for bi in borrow_items:
                if bi and len(bi) >= 6 and bi[1] == br[0] and bi[3].strip() == "กำลังยืม" and bi[-1] == "A":
                    book_titles.append(get_book_title(bi[2]))
            books_str = ", ".join(book_titles)
            
            active_borrows.append([br[0], member_name, books_str, borrow_date, return_date])
    
    if active_borrows:
        print("\n🔄 รายการยืมที่ยังไม่คืนครบ:")
        print(tabulate(active_borrows, headers=["BorrowID","ชื่อผู้ยืม","หนังสือที่ยังไม่คืน","วันที่ยืม","ต้องคืน"], tablefmt="grid"))
        return True
    else:
        print("ไม่มีรายการยืมที่ยังไม่คืนครบ")
        return False

def delete_borrow_record(borrow_id):
    """ลบรายการยืมและ borrow_items ที่เกี่ยวข้อง"""
    # ลบ borrow_items ที่เกี่ยวข้องก่อน
    borrow_items = read_file("borrow_items.txt", min_fields=6)
    for i, bi in enumerate(borrow_items):
        if bi and bi[1] == borrow_id and bi[-1] == "A":
            borrow_items[i][-1] = "D"  # ทำเครื่องหมายลบ
    write_file("borrow_items.txt", borrow_items)
    
    # ลบรายการยืมหลัก
    delete_record("borrows.txt", borrow_id)
    print("✔ ลบรายการยืมและคืนหนังสือทั้งหมดในรายการนี้เรียบร้อย")

def show_borrowed_books(borrow_id):
    """แสดงรายการหนังสือที่กำลังยืมอยู่ในรายการยืมนี้"""
    borrow_items = read_file("borrow_items.txt", min_fields=6)
    borrowed_books = []
    
    for bi in borrow_items:
        if bi and len(bi) >= 6 and bi[1] == borrow_id and bi[3].strip() == "กำลังยืม" and bi[-1] == "A":
            book_id = bi[2]
            book_title = get_book_title(book_id)
            borrowed_books.append([book_id, book_title])
    
    if borrowed_books:
        print(f"\n📖 หนังสือที่กำลังยืมในรายการ {borrow_id}:")
        print(tabulate(borrowed_books, headers=["BookID","ชื่อหนังสือ"], tablefmt="grid"))
        return True
    else:
        print(f"ไม่มีหนังสือที่กำลังยืมในรายการ {borrow_id}")
        return False

def return_book():
    # แสดงรายการยืมที่ยังไม่คืนครบก่อน
    if not show_active_borrows():
        return
    
    borrow_id = input("\nรหัสการยืม: ").strip()
    borrows = read_file("borrows.txt", min_fields=7)
    borrow_items = read_file("borrow_items.txt", min_fields=6)

    borrow = next((br for br in borrows if br and br[0] == borrow_id and br[-1] == "A"), None)
    if not borrow:
        print("✘ ไม่พบรหัสการยืม")
        return

    # แสดงรายการหนังสือที่กำลังยืมอยู่
    if not show_borrowed_books(borrow_id):
        return

    items_to_return = []
    print("\nกรอก BookID ที่ต้องการคืน (พิมพ์ 'done' เมื่อเสร็จ):")
    while True:
        book_id = input("BookID: ").strip()
        if book_id.lower() == "done":
            break
        found = False
        for i, bi in enumerate(borrow_items):
            # bi: [item_id, borrow_id, book_id, status, fine, "A"]
            if bi and len(bi) >= 6 and bi[1] == borrow_id and bi[2] == book_id and bi[3].strip() == "กำลังยืม":
                items_to_return.append(i)
                found = True
                print(f"✔ เพิ่ม {get_book_title(book_id)} ลงรายการคืน")
                break
        if not found:
            print("✘ ไม่พบ BookID หรือคืนไปแล้ว")
    
    if not items_to_return:
        print("✘ ไม่มีรายการที่จะคืน")
        return

    actual_return_date = input("วันที่คืนจริง (dd/mm/yyyy): ").strip()
    if not validate_date(actual_return_date):
        print("✘ รูปแบบวันที่ไม่ถูกต้อง")
        return

    # คืนหนังสือ + คำนวณค่าปรับ โดยใช้วันที่จาก borrow (br[2]=borrow_date, br[3]=return_date)
    for i in items_to_return:
        bi = borrow_items[i]
        ensure_min_len(bi, 6)
        fine = calculate_fine(borrow[2], borrow[3], actual_return_date)
        borrow_items[i][3] = "คืนแล้ว"
        borrow_items[i][4] = str(fine)

    write_file("borrow_items.txt", borrow_items)

    # เช็กว่าคืนครบทุกเล่มแล้วหรือยัง
    still_borrowed = any(bi and len(bi) >= 6 and bi[1] == borrow_id and bi[3].strip() == "กำลังยืม" and bi[-1] == "A" for bi in borrow_items)
    for i, br in enumerate(borrows):
        if br and br[0] == borrow_id:
            ensure_min_len(br, 6)
            borrows[i][5] = "กำลังยืม" if still_borrowed else "คืนแล้ว"
            break
    write_file("borrows.txt", borrows)

    print("✔ คืนหนังสือเรียบร้อย")


def view_borrows():
    borrows = read_file("borrows.txt", min_fields=7)
    borrow_items = read_file("borrow_items.txt", min_fields=6)
    members = read_file("members.txt", min_fields=4)
    books = read_file("books.txt", min_fields=5)  # แก้ไขจาก 4 เป็น 5

    table = []
    for br in borrows:
        if not br or br[-1] != "A":
            continue
        member_name = get_member_name(br[1])
        borrow_date = br[2]
        return_date = br[3]
        status = br[5] if len(br) > 5 else ""
        # หา titles ที่ยังสถานะกำลังยืมของ borrow นี้
        titles = []
        for bi in borrow_items:
            if bi and len(bi) >= 6 and bi[1] == br[0] and bi[3].strip() == "กำลังยืม" and bi[-1] == "A":
                titles.append(get_book_title(bi[2]))
        titles_str = ", ".join(titles) if titles else "-"
        # คำนวนค่าปรับรวมของรายการยืมนี้ (จาก borrow_items)
        fine_sum = 0.0
        for bi in borrow_items:
            if bi and bi[-1] == "A" and bi[1] == br[0]:
                try:
                    fine_sum += float(bi[4]) if str(bi[4]).replace('.', '', 1).isdigit() else 0
                except Exception:
                    continue
        table.append([br[0], member_name, titles_str, borrow_date, return_date, status, f"{fine_sum:.2f}"])

    if table:
        print(tabulate(table, headers=["BorrowID","Member","Books(กำลังยืม)","BorrowDate","ReturnDate","Status","TotalFine"], tablefmt="grid"))
    else:
        print("ไม่มีรายการการยืม")

# ------------ Enhanced Report ------------
def generate_report():
    books = read_file("books.txt", min_fields=5)  # แก้ไขจาก 4 เป็น 5
    members = read_file("members.txt", min_fields=4)
    borrows = read_file("borrows.txt", min_fields=7)
    borrow_items = read_file("borrow_items.txt", min_fields=6)

    print("\n📊 รายงานสรุประบบห้องสมุด")
    print("="*60)

    total_books = sum(1 for b in books if b and b[-1] == "A")
    total_members = sum(1 for m in members if m and m[-1] == "A")
    total_borrows = sum(1 for br in borrows if br and br[-1] == "A")

    active_borrows = 0
    completed_borrows = 0
    for br in borrows:
        if not br or br[-1] != "A":
            continue
        items = [bi for bi in borrow_items if bi and len(bi) >= 6 and bi[1] == br[0] and bi[-1] == "A"]
        if any(i[3].strip() == "กำลังยืม" for i in items):
            active_borrows += 1
        else:
            completed_borrows += 1

    total_fine = 0
    unpaid_fine = 0
    for bi in borrow_items:
        if not bi or bi[-1] != "A":
            continue
        try:
            fine = float(bi[4]) if str(bi[4]).replace('.', '', 1).isdigit() else 0
            total_fine += fine
            # ถ้าคืนแล้วแต่ยังมีค่าปรับ = ยังไม่ได้รับ
            if bi[3].strip() == "คืนแล้ว" and fine > 0:
                unpaid_fine += fine
        except Exception:
            continue

    # นับหนังสือที่กำลังถูกยืมอยู่
    books_currently_borrowed = 0  # หนังสือที่กำลังถูกยืมตอนนี้
    
    for bi in borrow_items:
        if bi and bi[-1] == "A" and bi[3].strip() == "กำลังยืม":
            books_currently_borrowed += 1

    print(f"📚 จำนวนหนังสือทั้งหมด: {total_books} เรื่อง")
    
    # คำนวณจำนวนเล่มรวมทั้งหมด
    total_copies_all = 0
    for b in books:
        if b and b[-1] == "A":
            total_copies_all += int(b[3]) if b[3].isdigit() else 0
    
    print(f"📖 จำนวนเล่มรวมทั้งหมด: {total_copies_all} เล่ม")
    print(f"👥 จำนวนสมาชิกทั้งหมด: {total_members} คน")
    print(f"📋 จำนวนการยืมทั้งหมด: {total_borrows} รายการ")
    print(f"🔄 กำลังยืมอยู่: {active_borrows} รายการ")
    print(f"✅ คืนแล้ว: {completed_borrows} รายการ")
    print(f"📘 หนังสือที่กำลังถูกยืมอยู่: {books_currently_borrowed} เล่ม")
    print(f"📗 หนังสือที่ว่างอยู่: {total_copies_all - books_currently_borrowed} เล่ม")
    print(f"💰 ค่าปรับรวมทั้งหมด: {total_fine:.2f} บาท")
    print(f"⚠️  ค่าปรับที่ยังไม่ได้รับ: {unpaid_fine:.2f} บาท")
    print("="*60)

    # หนังสือกำลังถูกยืม
    print("\n📖 หนังสือที่กำลังถูกยืม")
    borrowed_books = []
    for bi in borrow_items:
        if bi and bi[-1] == "A" and len(bi) >= 6 and bi[3].strip() == "กำลังยืม":
            borrow_id = bi[1]
            book_id = bi[2]
            br = next((b for b in borrows if b and b[0] == borrow_id and b[-1] == "A"), None)
            if br:
                member_name = get_member_name(br[1])
                borrow_date = br[2]
                return_date = br[3]
                try:
                    due_date = datetime.strptime(return_date, "%d/%m/%Y")
                    days_overdue = (datetime.now() - due_date).days
                    overdue_status = f"เกิน {days_overdue} วัน" if days_overdue > 0 else "ยังไม่เกิน"
                except Exception:
                    overdue_status = "ไม่ทราบ"
                book_title = get_book_title(book_id)
                borrowed_books.append([borrow_id, member_name, book_title, borrow_date, return_date, overdue_status])

    if borrowed_books:
        print(tabulate(borrowed_books, headers=["รหัสการยืม","ชื่อผู้ยืม","ชื่อหนังสือ","วันที่ยืม","ต้องคืน","สถานะ"], tablefmt="grid"))
    else:
        print("ไม่มีหนังสือที่กำลังถูกยืมอยู่")

    # รายละเอียดค่าปรับ
    print("\n💰 รายละเอียดค่าปรับ")
    fine_records = []
    for bi in borrow_items:
        if not bi or bi[-1] != "A":
            continue
        try:
            fine = float(bi[4]) if str(bi[4]).replace('.', '', 1).isdigit() else 0
            if fine > 0:
                borrow_id = bi[1]
                br = next((b for b in borrows if b and b[0] == borrow_id and b[-1] == "A"), None)
                if br:
                    member_name = get_member_name(br[1])
                    book_title = get_book_title(bi[2])
                    status = bi[3]
                    fine_records.append([member_name, book_title, f"{fine:.2f}", status])
        except Exception:
            continue

    if fine_records:
        print(tabulate(fine_records, headers=["ชื่อสมาชิก","ชื่อหนังสือ","ค่าปรับ (บาท)","สถานะ"], tablefmt="grid"))
    else:
        print("ไม่มีค่าปรับ")

    # หนังสือยอดนิยม
    print("\n📈 สถิติการยืม")
    book_borrow_count = {}
    for bi in borrow_items:
        if bi and bi[-1] == "A":
            book_borrow_count[bi[2]] = book_borrow_count.get(bi[2], 0) + 1

    if book_borrow_count:
        popular_books = sorted(book_borrow_count.items(), key=lambda x: x[1], reverse=True)[:5]
        print("หนังสือที่ถูกยืมมากที่สุด 5 อันดับ:")
        for i, (book_id, count) in enumerate(popular_books, 1):
            book_title = get_book_title(book_id)
            print(f"{i}. {book_title} - ถูกยืม {count} ครั้ง")
    print("="*60)

# ------------ Main Menu ------------
def main():
    while True:
        # เรียงเมนูใหม่: Book -> Member -> Borrow -> Report -> Exit
        data = ["1. Add Book","2. View Books","3. Update Book","4. Delete Book",
                "5. Add Member","6. View Members","7. Update Member","8. Delete Member",
                "9. Add Borrow","10. View Borrows","11. Return Book","12. Update Borrow",
                "13. Delete Borrow","14. Generate Report","0. Exit"]
        table = [data[i:i+4] for i in range(0,len(data),4)]
        print("\n\t\t\t\t===== เมนูหลัก =====")
        print(tabulate(table, tablefmt="grid"))

        choice = input("เลือกเมนู: ").strip()

        # Book Management (1-4)
        if choice == "1": add_book()
        elif choice == "2": view_books()
        elif choice == "3":
            # แสดงรายการหนังสือก่อนแก้ไข
            view_books()
            bid = input("\nใส่ BookID ที่ต้องการแก้ไข: ").strip()
            title = input("ชื่อหนังสือใหม่: ").strip()
            author = input("ผู้แต่งใหม่: ").strip()
            while True:
                try:
                    total_copies = int(input("จำนวนเล่มใหม่: ").strip())
                    if total_copies <= 0:
                        print("✘ จำนวนเล่มต้องมากกว่า 0")
                        continue
                    break
                except ValueError:
                    print("✘ กรุณาใส่ตัวเลข")
            update_record("books.txt", bid, [title, author, total_copies])
        elif choice == "4":
            # แสดงรายการหนังสือก่อนลบ
            view_books()
            bid = input("\nใส่ BookID ที่ต้องการลบ: ").strip()
            delete_record("books.txt", bid)
        # Member Management (5-8)
        elif choice == "5": add_member()
        elif choice == "6": view_members()
        elif choice == "7":
            # แสดงรายการสมาชิกก่อนแก้ไข
            view_members()
            mid = input("\nใส่ MemberID ที่ต้องการแก้ไข: ").strip()
            name = input("ชื่อสมาชิกใหม่: ").strip()
            phone = input("เบอร์ใหม่: ").strip()
            update_record("members.txt", mid, [name, phone])
        elif choice == "8":
            # แสดงรายการสมาชิกก่อนลบ
            view_members()
            mid = input("\nใส่ MemberID ที่ต้องการลบ: ").strip()
            delete_record("members.txt", mid)
        # Borrow Management (9-13)
        elif choice == "9": add_borrow()
        elif choice == "10": view_borrows()
        elif choice == "11": return_book()
        elif choice == "12":
            # แสดงรายการการยืมทั้งหมดก่อนแก้ไข
            view_borrows()
            borrow_id = input("\nใส่ BorrowID ที่ต้องการแก้ไข: ").strip()
            show_members_list()
            member_id = input("\nMemberID ใหม่: ").strip()
            borrow_date = input("วันที่ยืมใหม่ (dd/mm/yyyy): ").strip()
            return_date = input("วันที่ต้องคืนใหม่ (dd/mm/yyyy): ").strip()
            fine = input("ค่าปรับใหม่: ").strip()
            status = input("สถานะใหม่: ").strip()
            update_record("borrows.txt", borrow_id, [member_id, borrow_date, return_date, fine, status])
        elif choice == "13":
            # แสดงรายการการยืมทั้งหมดก่อนลบ
            view_borrows()
            borrow_id = input("\nใส่ BorrowID ที่ต้องการลบ: ").strip()
            delete_borrow_record(borrow_id)
        # Report & Exit
        elif choice == "14": generate_report()
        elif choice == "0":
            print("ออกจากระบบ")
            break
        else:
            print("✘ เลือกเมนูไม่ถูกต้อง")

if __name__ == "__main__":
    main()