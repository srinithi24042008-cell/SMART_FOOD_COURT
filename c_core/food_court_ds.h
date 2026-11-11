#ifndef FOOD_COURT_DS_H
#define FOOD_COURT_DS_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define MAX_NAME_LEN 128
#define MAX_STATUS_LEN 32
#define MAX_PAYMENT_LEN 32
typedef struct OrderItemNode {
    int item_id;
    char item_name[MAX_NAME_LEN];
    int quantity;
    double price;
    struct OrderItemNode* next;
} OrderItemNode;
typedef struct Order {
    int id;
    char bill_no[32];
    char token_no[32];
    int student_id;
    char student_name[MAX_NAME_LEN];
    double total_amount;
    char payment_method[MAX_PAYMENT_LEN];
    char payment_status[MAX_PAYMENT_LEN];
    char order_status[MAX_STATUS_LEN];
    long created_at; // unix timestamp
    OrderItemNode* items_head;
    struct Order* next; // For linked list / queue
} Order;
typedef struct {
    Order* front;
    Order* rear;
    int size;
} OrderQueue;
typedef struct {
    Order* head;
    int count;
} OrderLinkedList;
OrderQueue* create_queue(void);
void enqueue_order(OrderQueue* q, Order* order);
Order* dequeue_order(OrderQueue* q);
Order* peek_queue(OrderQueue* q);
int is_queue_empty(OrderQueue* q);
void free_queue(OrderQueue* q);
OrderLinkedList* create_linked_list(void);
void insert_order_sorted_by_time(OrderLinkedList* list, Order* order);
void append_order(OrderLinkedList* list, Order* order);
Order* search_order_by_token(OrderLinkedList* list, const char* token_no);
Order* search_order_by_bill(OrderLinkedList* list, const char* bill_no);
int delete_order_by_id(OrderLinkedList* list, int id);
void free_linked_list(OrderLinkedList* list);
void sort_orders_by_amount(Order** head, int ascending);
void sort_orders_by_time(Order** head, int ascending);
int binary_search_order_by_id(Order* orders[], int low, int high, int target_id);
Order* create_order(int id, const char* bill_no, const char* token_no,
                    int student_id, const char* student_name,
                    double total_amount, const char* payment_method,
                    const char* payment_status, const char* order_status,
                    long created_at);
void add_item_to_order(Order* order, int item_id, const char* item_name, int quantity, double price);
void free_order(Order* order);
void print_order_json(Order* order);
#endif
