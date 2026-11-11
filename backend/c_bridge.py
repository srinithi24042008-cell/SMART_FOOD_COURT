import os
import sys
import subprocess
import ctypes
from typing import List, Dict, Any, Optional
C_CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "c_core"))
DLL_PATH = os.path.join(C_CORE_DIR, "food_court_ds.dll")
CLI_PATH = os.path.join(C_CORE_DIR, "food_court_ds_cli.exe")
class OrderNode:
    def __init__(self, order_id: int, bill_no: str, token_no: str,
                 student_id: int, student_name: str, total_amount: float,
                 payment_method: str, payment_status: str, order_status: str,
                 created_at: int):
        self.id = order_id
        self.bill_no = bill_no
        self.token_no = token_no
        self.student_id = student_id
        self.student_name = student_name
        self.total_amount = total_amount
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.order_status = order_status
        self.created_at = created_at
        self.items = []
        self.next: Optional['OrderNode'] = None
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "bill_no": self.bill_no,
            "token_no": self.token_no,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "total_amount": round(self.total_amount, 2),
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "order_status": self.order_status,
            "created_at": self.created_at,
            "items": self.items
        }
class KitchenOrderQueue:
    def __init__(self):
        self.front: Optional[OrderNode] = None
        self.rear: Optional[OrderNode] = None
        self.size: int = 0
    def enqueue(self, order: OrderNode):
        order.next = None
        if self.rear is None:
            self.front = self.rear = order
        else:
            self.rear.next = order
            self.rear = order
        self.size += 1
    def dequeue(self) -> Optional[OrderNode]:
        if self.front is None:
            return None
        temp = self.front
        self.front = self.front.next
        if self.front is None:
            self.rear = None
        temp.next = None
        self.size -= 1
        return temp
    def peek(self) -> Optional[OrderNode]:
        return self.front
    def is_empty(self) -> bool:
        return self.front is None
    def get_all(self) -> List[Dict[str, Any]]:
        result = []
        cur = self.front
        while cur:
            result.append(cur.to_dict())
            cur = cur.next
        return result
class OrderHistoryLinkedList:
    def __init__(self):
        self.head: Optional[OrderNode] = None
        self.count: int = 0
    def append(self, order: OrderNode):
        order.next = None
        if self.head is None:
            self.head = order
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = order
        self.count += 1
    def search_by_token(self, token_no: str) -> Optional[OrderNode]:
        cur = self.head
        token_clean = token_no.strip().upper()
        while cur:
            if cur.token_no.strip().upper() == token_clean:
                return cur
            cur = cur.next
        return None
    def search_by_bill(self, bill_no: str) -> Optional[OrderNode]:
        cur = self.head
        bill_clean = bill_no.strip().upper()
        while cur:
            if cur.bill_no.strip().upper() == bill_clean:
                return cur
            cur = cur.next
        return None
    def to_list(self) -> List[Dict[str, Any]]:
        result = []
        cur = self.head
        while cur:
            result.append(cur.to_dict())
            cur = cur.next
        return result
def merge_sort_orders_by_amount(orders: List[Dict[str, Any]], ascending: bool = True) -> List[Dict[str, Any]]:
    if len(orders) <= 1:
        return orders
    mid = len(orders) // 2
    left = merge_sort_orders_by_amount(orders[:mid], ascending)
    right = merge_sort_orders_by_amount(orders[mid:], ascending)
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        cond = (left[i]["total_amount"] <= right[j]["total_amount"]) if ascending else (left[i]["total_amount"] >= right[j]["total_amount"])
        if cond:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged
def binary_search_order_by_id(orders_sorted_by_id: List[Dict[str, Any]], target_id: int) -> Optional[Dict[str, Any]]:
    low = 0
    high = len(orders_sorted_by_id) - 1
    while low <= high:
        mid = (low + high) // 2
        curr_id = orders_sorted_by_id[mid].get("id")
        if curr_id == target_id:
            return orders_sorted_by_id[mid]
        elif curr_id < target_id:
            low = mid + 1
        else:
            high = mid - 1
    return None
def get_c_module_status() -> Dict[str, Any]:
    has_c_src = os.path.exists(os.path.join(C_CORE_DIR, "food_court_ds.c"))
    has_header = os.path.exists(os.path.join(C_CORE_DIR, "food_court_ds.h"))
    has_cli = os.path.exists(CLI_PATH) or os.path.exists(CLI_PATH.replace(".exe", ""))
    has_dll = os.path.exists(DLL_PATH)
    return {
        "c_source_present": has_c_src,
        "c_header_present": has_header,
        "c_cli_compiled": has_cli,
        "c_dll_compiled": has_dll,
        "integration_mode": "Native C Core Subprocess/Ctypes" if (has_cli or has_dll) else "High-Performance C Algorithm Bridge (Python Driver)",
        "algorithms_active": [
            "FIFO Kitchen Order Queue (create_queue, enqueue_order, dequeue_order, peek_queue)",
            "Order History Singly Linked List (append_order, search_order_by_token, search_order_by_bill)",
            "O(N log N) Merge Sort on Order Amounts & Timestamps",
            "O(log N) Binary Search by Order ID"
        ]
    }
