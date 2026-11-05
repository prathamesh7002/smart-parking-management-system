#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

const int MAX_SLOTS = 20;
const int TABLE_SIZE = 11;

struct Vehicle
{
    string number, owner, type;
    int slot = -1;
};

// array- parking slot
string slots[MAX_SLOTS];

// Queue(fifo)-linked list with front and rear end

struct QueueNode
{
    Vehicle v;
    QueueNode *next;
};

struct WatingQueue
{
    QueueNode *front = nullptr;
    QueueNode *rear = nullptr;

    int size = 0;
    // return true is queue is empty
    bool isEmpty()
    {
        return size == 0;
    }
    // adding the vehical to the wating list in the back
    void enqueue(Vehicle v)
    {
        QueueNode *n = new QueueNode{v, nullptr};

        if (rear)
        {
            rear->next = n;
        }
        else
        {
            front = n;
        }
        rear = n;
        size++;
    }
    // removing the vehical from the front

    Vehicle dequeue()
    {
        QueueNode *n = front;
        Vehicle v = n->v;
        front = n->next;
        if (!front)
            rear = nullptr;
        delete n;
        size--;
        return v;
    }
    // to check the given number is in the wating queue or not
    bool contains(string no)
    {
        for (QueueNode *p = front; p; p->next)
        {
            if (p->v.number == no)
            {
                return true;
            }
            return false;
        }
    }

    void clear()
    {
        while (!isempty())
        {
            dequeue();
        }
    }
};
// stack(lifo)-array + top index
//      A slot is pushed only when it becomes free, and the array is scanned
//      only when the stack is empty, so the stack can never overflow.

struct VacatedStack
{
    int data[MAX_SLOTS];
    int top = -1;

    bool isEmpty()
    {
        return top == -1;
    }
    void push(int s)
    {
        data[++top] = s;
    }
    int pop()
    {
        return data[top--];
    }
    void clear()
    {
        top = -1;
    }
};

// HASH TABLE - separate chaining (key = vehicle number)
// hash(key) = (h * 31 + character )% TABLE_SIZE

struct HashNode
{
    Vehicle v;
    HashNode* next;
};

struct HashTable{
HashNode* bucket[TABLE_SIZE]={};

int hashOf(string key){
    int h  = 0 ;
    for(char c:key)
    {
        h = (h * 31 +(unsigned char)c)% TABLE_SIZE;
    }
}
};