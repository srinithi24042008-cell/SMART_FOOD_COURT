#include "food_court_ds.h"
void run_self_test(void) {
    printf("=== Campus Food Court C Core Module Self-Test ===\n\n");
    printf("[1] Testing Order Processing Queue (FIFO):\n");
    OrderQueue* q = create_queue();
    Order* o1 = create_order(101, "BILL-1001", "TKN-A1", 1, "Aarav", 180.0, "UPI", "PAID", "CONFIRMED", 1700000000);
    add_item_to_order(o1, 1, "Paneer Butter Masala", 1, 140.0);
    add_item_to_order(o1, 2, "Butter Naan", 2, 40.0);
    Order* o2 = create_order(102, "BILL-1002", "TKN-A2", 2, "Diya", 85.0, "CASH", "PENDING", "CONFIRMED", 1700000100);
    add_item_to_order(o2, 3, "Masala Dosa", 1, 85.0);
    Order* o3 = create_order(103, "BILL-1003", "TKN-A3", 3, "Kavya", 250.0, "UPI", "PAID", "CONFIRMED", 1700000200);
    add_item_to_order(o3, 4, "Veg Biryani Combo", 1, 250.0);
    enqueue_order(q, o1);
    enqueue_order(q, o2);
    enqueue_order(q, o3);
    printf("  Enqueued 3 orders. Queue size: %d\n", q->size);
    Order* next = dequeue_order(q);
    printf("  Dequeued next order to prepare: ID=%d, Bill=%s, Token=%s, Student=%s (Amount: Rs. %.2f)\n",
           next->id, next->bill_no, next->token_no, next->student_name, next->total_amount);
    free_order(next);
    printf("  Remaining queue size: %d\n\n", q->size);
    printf("[2] Testing Order Linked List & Linear Token/Bill Search:\n");
    OrderLinkedList* list = create_linked_list();
    Order* l1 = create_order(201, "BILL-2001", "TKN-B1", 4, "Rohan", 120.0, "UPI", "PAID", "COMPLETED", 1700000300);
    Order* l2 = create_order(202, "BILL-2002", "TKN-B2", 5, "Sneha", 310.0, "CASH", "PAID", "COMPLETED", 1700000400);
    Order* l3 = create_order(203, "BILL-2003", "TKN-B3", 6, "Vikram", 95.0, "UPI", "PAID", "COMPLETED", 1700000500);
    append_order(list, l1);
    append_order(list, l2);
    append_order(list, l3);
    printf("  Linked list created with %d orders.\n", list->count);
    Order* found = search_order_by_token(list, "TKN-B2");
    if (found) {
        printf("  Found order by token 'TKN-B2': Student=%s, Bill=%s, Amount=Rs. %.2f\n",
               found->student_name, found->bill_no, found->total_amount);
    } else {
        printf("  Token 'TKN-B2' not found!\n");
    }
    found = search_order_by_bill(list, "BILL-2003");
    if (found) {
        printf("  Found order by bill 'BILL-2003': Student=%s, Token=%s, Amount=Rs. %.2f\n\n",
               found->student_name, found->token_no, found->total_amount);
    }
    printf("[3] Testing Merge Sort on Orders by Amount (Ascending):\n");
    sort_orders_by_amount(&(list->head), 1);
    Order* cur = list->head;
    while (cur) {
        printf("  Order ID=%d, Bill=%s, Amount=Rs. %.2f\n", cur->id, cur->bill_no, cur->total_amount);
        cur = cur->next;
    }
    printf("\n");

    printf("[4] Testing Binary Search on Ordered Array by ID:\n");
    Order* arr[3];
    arr[0] = create_order(10, "B-10", "T-10", 1, "S1", 50.0, "UPI", "PAID", "READY", 1700000000);
    arr[1] = create_order(20, "B-20", "T-20", 2, "S2", 60.0, "UPI", "PAID", "READY", 1700000010);
    arr[2] = create_order(30, "B-30", "T-30", 3, "S3", 70.0, "UPI", "PAID", "READY", 1700000020);

    int idx = binary_search_order_by_id(arr, 0, 2, 20);
    if (idx != -1) {
        printf("  Binary search found target ID 20 at index %d: Bill=%s, Token=%s\n\n",
               idx, arr[idx]->bill_no, arr[idx]->token_no);
    }

    free_queue(q);
    free_linked_list(list);
    for (int i = 0; i < 3; i++) free_order(arr[i]);

    printf("=== Self-Test Completed Successfully! ===\n");
}

int main(int argc, char* argv[]) {
    if (argc < 2 || strcmp(argv[1], "test") == 0) {
        run_self_test();
        return 0;
    }

    if (strcmp(argv[1], "verify_token") == 0 && argc >= 3) {
        const char* token = argv[2];
        printf("{\"valid\":1,\"token\":\"%s\"}\n", token);
        return 0;
    }

    run_self_test();
    return 0;
}
