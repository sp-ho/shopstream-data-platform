import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline as BeamTestPipeline # alias the Beam class as BeamTestPipeline to avoid naming conflicts with the custom TestPipeline class
from apache_beam.testing.util import assert_that, equal_to

def test_pipeline_processes_test_messages():
    messages = [
        b'{"event_id":"test-001","event_type":"product_viewed"}',
        b'{"event_id":"test-002","event_type":"cart_added"}',
    ]

    with BeamTestPipeline() as pipeline:
        output = (
            pipeline
            | "CreateTestMessages" >> beam.Create(messages)
            | "DecodeMessages" >> beam.Map(
                lambda message: message.decode("utf-8")
            )
        )

        assert_that(
            output,
            equal_to(
                [
                    '{"event_id":"test-001","event_type":"product_viewed"}',
                    '{"event_id":"test-002","event_type":"cart_added"}',
                ]
            ),
        )