import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from graphql import GraphQLError

from .models import Customer, Product, Order
import re


# Object Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer


class ProductType(DjangoObjectType):
    class Meta:
        model = Product


class OrderType(DjangoObjectType):
    class Meta:
        model = Order


# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()



# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        if Customer.objects.filter(email=input.email).exists():
            raise GraphQLError("Email already exists")

        if input.phone:
            import re
            pattern = r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$'
            if not re.match(pattern, input.phone):
                raise GraphQLError("Invalid phone format")

        customer = Customer.objects.create(**input)
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    @transaction.atomic
    def mutate(root, info, inputs):
        customers = []
        errors = []

        for input in inputs:
            try:
                if input.phone and not re.match(r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$', input.phone):
                    raise ValidationError("Invalid phone format")

                customer = Customer(
                    name=input.name,
                    email=input.email,
                    phone=input.phone
                )
                customer.full_clean()
                customer.save()
                customers.append(customer)
            except Exception as e:
                errors.append(f"Failed to create customer {input.email}: {str(e)}")

        return BulkCreateCustomers(customers=customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input):
        if input.price <= 0:
            raise GraphQLError("Price must be positive")
        if input.stock < 0:
            raise GraphQLError("Stock cannot be negative")
        try:
            product = Product(
                name=input.name,
                price=input.price,
                stock=input.stock if input.stock is not None else 0
            )
            product.full_clean()
            product.save()
            return CreateProduct(product=product)
        except Exception as e:
            raise ValidationError(str(e))


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)

            products = []
            total_amount = 0
            for product_id in input.product_ids:
                product = Product.objects.get(pk=product_id)
                products.append(product)
                total_amount += product.price

            if not products:
                raise ValidationError("At least one product is required")

            order = Order(
                customer=customer,
                total_amount=total_amount,
                order_date=input.order_date if input.order_date else None
            )
            order.save()
            order.products.set(products)

            return CreateOrder(order=order)
        except Customer.DoesNotExist:
            raise ValidationError("Customer does not exist")
        except Product.DoesNotExist:
            raise ValidationError("One or more products do not exist")
        except Exception as e:
            raise ValidationError(str(e))


class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(root, info):
        return "Hello, GraphQL!"


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)