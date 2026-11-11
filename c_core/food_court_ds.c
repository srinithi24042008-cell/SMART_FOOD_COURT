#include "food_court_ds.h"
Order* create_order(int id, const char* bill_no, const char* token_no,
                    int student_id, const char* student_name,
                    double total_amount, const char* payment_method,
                    const char* payment_status, const char* order_status,
                    long created_at) {
    Order* ord = (Order*)malloc(sizeof(Order));
    if (!ord) return NULL;
    ord->id = id;
    strncpy(ord->bill_no, bill_no ? bill_no : "", sizeof(ord->bill_no) - 1);
    ord->bill_no[sizeof(ord->bill_no) - 1] = '\0';
    strncpy(ord->token_no, token_no ? token_no : "", sizeof(ord->token_no) - 1);
    ord->token_no[sizeof(ord->token_no) - 1] = '\0';
    ord->student_id = student_id;
    strncpy(ord->student_name, student_name ? student_name : "", sizeof(ord->student_name) - 1);
    ord->student_name[sizeof(ord->student_name) - 1] = '\0';
    ord->total_amount = total_amount;
    strncpy(ord->payment_method, payment_method ? payment_method : "", sizeof(ord->payment_method) - 1);
    ord->payment_method[sizeof(ord->payment_method) - 1] = '\0';
    strncpy(ord->payment_status, payment_status ? payment_status : "", sizeof(ord->payment_status) - 1);
    ord->payment_status[sizeof(ord->payment_status) - 1] = '\0';
    strncpy(ord->order_status, order_status ? order_status : "", sizeof(ord->order_status) - 1);
    ord->order_status[sizeof(ord->order_status) - 1] = '\0';
    ord->created_at = created_at;
    ord->items_head = NULL;
    ord->next = NULL;
    return ord;
}
void add_item_to_order(Order* order, int item_id, const char* item_name, int quantity, double price) {
    if (!order) return;
    OrderItemNode* node = (OrderItemNode*)malloc(sizeof(OrderItemNode));
    if (!node) return;
    node->item_id = item_id;
    strncpy(node->item_name, item_name ? item_name : "", sizeof(node->item_name) - 1);
    node->item_name[sizeof(node->item_name) - 1] = '\0';
    node->quantity = quantity;
    node->price = price;
    node->next = order->items_head;
    order->items_head = node;
}
void free_order(Order* order) {
    if (!order) return;
    OrderItemNode* cur = order->items_head;
    while (cur) {
        OrderItemNode* tmp = cur;
        cur = cur->next;
        free(tmp);
    }
    free(order);
}
OrderQueue* create_queue(void) {
    OrderQueue* q = (OrderQueue*)malloc(sizeof(OrderQueue));
    if (q) {
        q->front = NULL;
        q->rear = NULL;
        q->size = 0;
    }
    return q;
}
void enqueue_order(OrderQueue* q, Order* order) {
    if (!q || !order) return;
    order->next = NULL;
    if (q->rear == NULL) {
        q->front = q->rear = order;
    } else {
        q->rear->next = order;
        q->rear = order;
    }
    q->size++;
}
Order* dequeue_order(OrderQueue* q) {
    if (!q || !q->front) return NULL;
    Order* temp = q->front;
    q->front = q->front->next;
    if (q->front == NULL) {
        q->rear = NULL;
    }
    temp->next = NULL;
    q->size--;
    return temp;
}
Order* peek_queue(OrderQueue* q) {
    if (!q) return NULL;
    return q->front;
}
int is_queue_empty(OrderQueue* q) {
    return (q == NULL || q->front == NULL);
}
void free_queue(OrderQueue* q) {
    if (!q) return;
    Order* cur = q->front;
    while (cur) {
        Order* tmp = cur;
        cur = cur->next;
        free_order(tmp);
    }
    free(q);
}
OrderLinkedList* create_linked_list(void) {
    OrderLinkedList* list = (OrderLinkedList*)malloc(sizeof(OrderLinkedList));
    if (list) {
        list->head = NULL;
        list->count = 0;
    }
    return list;
}
void append_order(OrderLinkedList* list, Order* order) {
    if (!list || !order) return;
    order->next = NULL;
    if (!list->head) {
        list->head = order;
    } else {
        Order* cur = list->head;
        while (cur->next) {
            cur = cur->next;
        }
        cur->next = order;
    }
    list->count++;
}
void insert_order_sorted_by_time(OrderLinkedList* list, Order* order) {
    if (!list || !order) return;
    if (!list->head || order->created_at >= list->head->created_at) {
        order->next = list->head;
        list->head = order;
    } else {
        Order* cur = list->head;
        while (cur->next && cur->next->created_at > order->created_at) {
            cur = cur->next;
        }
        order->next = cur->next;
        cur->next = order;
    }
    list->count++;
}
Order* search_order_by_token(OrderLinkedList* list, const char* token_no) {
    if (!list || !token_no) return NULL;
    Order* cur = list->head;
    while (cur) {
        if (strcmp(cur->token_no, token_no) == 0) {
            return cur;
        }
        cur = cur->next;
    }
    return NULL;
}
Order* search_order_by_bill(OrderLinkedList* list, const char* bill_no) {
    if (!list || !bill_no) return NULL;
    Order* cur = list->head;
    while (cur) {
        if (strcmp(cur->bill_no, bill_no) == 0) {
            return cur;
        }
        cur = cur->next;
    }
    return NULL;
}
int delete_order_by_id(OrderLinkedList* list, int id) {
    if (!list || !list->head) return 0;
    Order* cur = list->head;
    Order* prev = NULL;
    while (cur && cur->id != id) {
        prev = cur;
        cur = cur->next;
    }
    if (!cur) return 0;
    if (!prev) {
        list->head = cur->next;
    } else {
        prev->next = cur->next;
    }
    free_order(cur);
    list->count--;
    return 1;
}
void free_linked_list(OrderLinkedList* list) {
    if (!list) return;
    Order* cur = list->head;
    while (cur) {
        Order* tmp = cur;
        cur = cur->next;
        free_order(tmp);
    }
    free(list);
}
static void split_list(Order* source, Order** frontRef, Order** backRef) {
    Order* fast;
    Order* slow;
    slow = source;
    fast = source->next;
    while (fast != NULL) {
        fast = fast->next;
        if (fast != NULL) {
            slow = slow->next;
            fast = fast->next;
        }
    }
    *frontRef = source;
    *backRef = slow->next;
    slow->next = NULL;
}
static Order* merge_amount(Order* a, Order* b, int ascending) {
    Order* result = NULL;
    if (a == NULL) return b;
    if (b == NULL) return a;
    int condition = ascending ? (a->total_amount <= b->total_amount) : (a->total_amount >= b->total_amount);
    if (condition) {
        result = a;
        result->next = merge_amount(a->next, b, ascending);
    } else {
        result = b;
        result->next = merge_amount(a, b->next, ascending);
    }
    return result;
}
void sort_orders_by_amount(Order** headRef, int ascending) {
    Order* head = *headRef;
    Order* a;
    Order* b;
    if ((head == NULL) || (head->next == NULL)) return;
    split_list(head, &a, &b);
    sort_orders_by_amount(&a, ascending);
    sort_orders_by_amount(&b, ascending);
    *headRef = merge_amount(a, b, ascending);
}
static Order* merge_time(Order* a, Order* b, int ascending) {
    Order* result = NULL;
    if (a == NULL) return b;
    if (b == NULL) return a;
    int condition = ascending ? (a->created_at <= b->created_at) : (a->created_at >= b->created_at);
    if (condition) {
        result = a;
        result->next = merge_time(a->next, b, ascending);
    } else {
        result = b;
        result->next = merge_time(a, b->next, ascending);
    }
    return result;
}
void sort_orders_by_time(Order** headRef, int ascending) {
    Order* head = *headRef;
    Order* a;
    Order* b;
    if ((head == NULL) || (head->next == NULL)) return;
    split_list(head, &a, &b);
    sort_orders_by_time(&a, ascending);
    sort_orders_by_time(&b, ascending);
    *headRef = merge_time(a, b, ascending);
}
int binary_search_order_by_id(Order* orders[], int low, int high, int target_id) {
    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (orders[mid]->id == target_id) return mid;
        if (orders[mid]->id < target_id) low = mid + 1;
        else high = mid - 1;
    }
    return -1;
}
void print_order_json(Order* order) {
    if (!order) {
        printf("null");
        return;
    }
    printf("{\"id\":%d,\"bill_no\":\"%s\",\"token_no\":\"%s\",\"student_id\":%d,\"student_name\":\"%s\",\"total_amount\":%.2f,\"payment_method\":\"%s\",\"payment_status\":\"%s\",\"order_status\":\"%s\",\"created_at\":%ld}",
           order->id, order->bill_no, order->token_no, order->student_id, order->student_name,
           order->total_amount, order->payment_method, order->payment_status, order->order_status, order->created_at);
}
